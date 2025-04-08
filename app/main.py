import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Depends
from app.schemas import SecretCreate, SecretResponse, GetSecretResponse, DeleteResponse
from app.utils import encrypt_secret, decrypt_secret
from app.crud import log_action
from app.database import get_db, engine
from app.models import Base
import asyncio

app = FastAPI(title="One-time Secrets Service")

# Create database tables and initialize in-memory cache on startup.
@app.on_event("startup")
async def startup():
    # Create tables in the database.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Initialize in-memory cache and start cleanup background task.
    app.state.secret_cache = {}
    app.state.cache_lock = asyncio.Lock()
    app.state.cleanup_task = asyncio.create_task(cleanup_expired_secrets())

# Cancel background task on shutdown.
@app.on_event("shutdown")
async def shutdown():
    app.state.cleanup_task.cancel()
    try:
        await app.state.cleanup_task
    except asyncio.CancelledError:
        pass

# In-memory secret cache structure:
# {
#   secret_key: {
#       "encrypted_secret": str,
#       "passphrase": Optional[str],
#       "expires_at": datetime,
#       "retrieved": bool
#   }
# }

# Middleware to disable client caching.
@app.middleware("http")
async def no_cache_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.post("/secret", response_model=SecretResponse)
async def create_secret(secret_data: SecretCreate, request: Request, db=Depends(get_db)):
    secret_key = str(uuid.uuid4())
    # Ensure ttl is at least 300 seconds (5 minutes).
    ttl = secret_data.ttl_seconds if secret_data.ttl_seconds and secret_data.ttl_seconds >= 300 else 300
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    encrypted = encrypt_secret(secret_data.secret)
    async with app.state.cache_lock:
        app.state.secret_cache[secret_key] = {
            "encrypted_secret": encrypted,
            "passphrase": secret_data.passphrase,
            "expires_at": expires_at,
            "retrieved": False
        }
    # Log creation action.
    await log_action(db, secret_key, "create", ip_address=request.client.host, metadata={"ttl_seconds": ttl})
    return SecretResponse(secret_key=secret_key)

@app.get("/secret/{secret_key}", response_model=GetSecretResponse)
async def get_secret(secret_key: str, request: Request, db=Depends(get_db)):
    async with app.state.cache_lock:
        secret_entry = app.state.secret_cache.get(secret_key)
        if not secret_entry:
            raise HTTPException(status_code=404, detail="Secret not found or already retrieved/deleted")
        if datetime.utcnow() > secret_entry["expires_at"]:
            # Remove expired secret.
            del app.state.secret_cache[secret_key]
            await log_action(db, secret_key, "expire", ip_address=request.client.host)
            raise HTTPException(status_code=404, detail="Secret expired")
        if secret_entry["retrieved"]:
            raise HTTPException(status_code=404, detail="Secret already retrieved")
        # Mark secret as retrieved and remove it from cache.
        secret_entry["retrieved"] = True
        decrypted = decrypt_secret(secret_entry["encrypted_secret"])
        del app.state.secret_cache[secret_key]
    # Log retrieval action.
    await log_action(db, secret_key, "retrieve", ip_address=request.client.host)
    return GetSecretResponse(secret=decrypted)

@app.delete("/secret/{secret_key}", response_model=DeleteResponse)
async def delete_secret(secret_key: str, request: Request, db=Depends(get_db)):
    async with app.state.cache_lock:
        secret_entry = app.state.secret_cache.get(secret_key)
        if not secret_entry:
            raise HTTPException(status_code=404, detail="Secret not found or already deleted/retrieved")
        # Remove the secret immediately.
        del app.state.secret_cache[secret_key]
    # Log deletion action.
    await log_action(db, secret_key, "delete", ip_address=request.client.host)
    return DeleteResponse(status="secret_deleted")

# Background task to periodically clear expired secrets.
async def cleanup_expired_secrets():
    while True:
        await asyncio.sleep(60)  # Run cleanup every minute.
        async with app.state.cache_lock:
            now = datetime.utcnow()
            expired_keys = [key for key, entry in app.state.secret_cache.items() if now > entry["expires_at"]]
            for key in expired_keys:
                del app.state.secret_cache[key]
                # Optionally, log expiration events if needed.
