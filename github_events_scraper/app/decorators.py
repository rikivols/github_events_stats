import traceback
import logging
import time
from typing import Callable
from functools import wraps

from requests import Response
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.helpers import time_response


def track_response(func: Callable[..., Response]) -> Callable[..., Response]:
    @wraps(func)
    def inner(*args, **kwargs) -> Response:
        request_start = time.time()

        request_url = args[1]

        log_message = f"Request to url: {request_url}, took: "

        try:
            response = func(*args, **kwargs)

            msg = f"{log_message}{time_response(request_start)}s, status code: {response.status_code}"

            if response.ok:
                logging.info(msg)
            else:
                logging.warning(f"{msg}, response: {response.text}")

            return response
        except Exception as e:
            # most likely "Max retries exceeded" from the retry adapter
            logging.error(
                f"{log_message}{time_response(request_start)}s, ERROR: {e}, traceback: {traceback.format_exc()}"
            )
            raise

    return inner


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
