
import time
import datetime
import logging

from app.config import Config


def time_response(time_: float):
    return round(time.time() - time_, 2)


def calculate_days_ago(datetime_input: datetime.datetime) -> int:
    datetime_difference = datetime.datetime.now(datetime.timezone.utc) - datetime_input
    return datetime_difference.days


def convert_github_datetime(datetime_input: str) -> datetime.datetime:
    input_time = datetime.datetime.strptime(datetime_input, "%Y-%m-%dT%H:%M:%SZ")
    return input_time.replace(tzinfo=datetime.timezone.utc)


def convert_to_github_datetime(datetime_input: datetime.datetime) -> str:
    return datetime_input.strftime("%Y-%m-%dT%H:%M:%SZ")


def set_logger(config: Config):
    logging_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging_level_map.get(config.LOGGING_LEVEL, "warning"))
