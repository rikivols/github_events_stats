
import os

from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

from app import config

Base = declarative_base()

class GithubEvent(Base):
    __tablename__ = os.getenv("DB_NAME", config.database_name)

    id = Column(String(50), primary_key=True, unique=True)
    type = Column(String(255))
    created_at = Column(DateTime, index=True)
    repository = Column(String(255))

