
from sqlalchemy import Column, Index, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GithubEvent(Base):
    __tablename__ = "GithubEvents"

    id = Column(String(50), primary_key=True, unique=True)
    type = Column(String(255))
    created_at = Column(DateTime, index=True)
    repository = Column(String(255))
