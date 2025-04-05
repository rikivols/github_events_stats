
import time
import datetime
import os

from app import config


def time_response(time_: float):
    return round(time.time() - time_, 2)


def calculate_days_ago(datetime_input: datetime.datetime) -> int:
    datetime_difference = datetime.datetime.now(datetime.UTC) - datetime_input
    return datetime_difference.days


def convert_github_datetime(datetime_input: str) -> datetime.datetime:
    input_time = datetime.datetime.strptime(datetime_input, "%Y-%m-%dT%H:%M:%SZ")
    return input_time.replace(tzinfo=datetime.timezone.utc)


def get_postgre_url() -> str:
    db_user = os.getenv("DB_USER", config.database_user)
    db_password = os.getenv("DB_PASSWORD", config.database_password)
    db_host = os.getenv("DB_HOST", config.database_host)
    db_port = os.getenv("DB_PORT", config.database_port)
    db_name = os.getenv("DB_NAME", config.database_name)

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
