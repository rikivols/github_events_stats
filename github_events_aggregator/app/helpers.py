
import time
import datetime

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def time_response(time_: float):
    return round(time.time() - time_, 2)


def calculate_days_ago(datetime_input: str) -> int:
    input_time = datetime.datetime.strptime(datetime_input, "%Y-%m-%dT%H:%M:%SZ")
    input_time = input_time.replace(tzinfo=datetime.timezone.utc)
    datetime_difference = datetime.datetime.now(datetime.UTC) - input_time
    return datetime_difference.days
