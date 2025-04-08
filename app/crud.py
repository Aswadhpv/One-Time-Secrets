from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Log
from datetime import datetime
from typing import Optional

async def log_action(
    db: AsyncSession,
    secret_key: str,
    action: str,
    ip_address: Optional[str] = None,
    metadata: Optional[dict] = None
):
    log_entry = Log(
        secret_key=secret_key,
        action=action,
        timestamp=datetime.utcnow(),
        ip_address=ip_address,
        log_metadata=metadata  # updated field name
    )
    db.add(log_entry)
    await db.commit()
