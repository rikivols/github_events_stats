
import os

from typing import Callable
from functools import wraps

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def get_postgre_url() -> str:
    db_user = os.getenv("DATABASE_USER")
    db_password = os.getenv("DATABASE_PASSWORD")
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT")
    db_name = os.getenv("DATABASE_NAME")
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def postgre_session(func: Callable[..., any]) -> Callable[..., any]:
    @wraps(func)
    def inner(*args, **kwargs) -> any:
        class_instance = args[0]
        engine: Engine = class_instance.db_engine

        with sessionmaker(bind=engine, autoflush=False, autocommit=False)() as session:
            try:
                response = func(*args, session=session, **kwargs)
                return response
            except Exception:
                session.rollback()
                raise

    return inner


