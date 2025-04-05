import traceback
import logging
import time
from typing import Callable

from requests import Response

from app.helpers import time_response


def track_response(func: Callable[..., Response]) -> Callable[..., Response]:
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
            raise e

    return inner
