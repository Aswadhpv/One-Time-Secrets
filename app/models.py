from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    secret_key = Column(String, index=True)
    action = Column(String)  # actions: create, retrieve, delete, expire
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    log_metadata = Column(JSON, nullable=True)  # renamed to avoid conflict
