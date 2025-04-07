from typing import get_type_hints
from os import environ as env
import ast

from dotenv import load_dotenv


class ConfigError(Exception):
    pass


class Config:
    # Github
    GITHUB_REPOSITORIES: list = None
    GITHUB_AUTHENTICATION_TOKENS: list = None
    GITHUB_MAX_REPOSITORIES: int = 5
    GITHUB_REFRESH_RATE: int = 3600
    GITHUB_API_URL: str = "https://api.github.com"

    # Request
    REQUEST_TIMEOUT: int = 60
    REQUEST_MAX_RETRY: int = 3
    REQUEST_BACKOFF_FACTOR: int = 1
    REQUEST_STATUS_FORCELIST: list = [501, 502, 503, 504]

    # Aggregator
    AGGREGATOR_ROLLING_DAYS: int = 7
    AGGREGATOR_ROLLING_EVENTS: int = 500

    # Logging
    LOGGING_LEVEL: str = "warning"

    _instance = None

    # making it a singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        load_dotenv()
        for field in self.__annotations__:
            if not field.isupper():
                continue

            # Validate if mandatory environment variables are provided
            default_value = getattr(self, field, None)
            if default_value is None and env.get(field) is None:
                raise ConfigError("The {} field is required".format(field))

            # Parse environment variables
            try:
                var_type = get_type_hints(Config)[field]
                if var_type == bool:
                    value = self._parse_bool(env.get(field, default_value))
                elif var_type == list:
                    value = self._parse_list(env.get(field, default_value))
                elif var_type == dict:
                    value = self._parse_dict(env.get(field, default_value))
                elif var_type == str:
                    value = self._parse_str(env.get(field, default_value))
                else:
                    value = var_type(env.get(field, default_value))

                self.__setattr__(field, value)
            except ValueError:
                raise ConfigError(
                    'Unable to cast value of "{}" to type "{}" for "{}" field'.format(
                        env[field], var_type, field
                    )
                )

    def _parse_bool(self, val: str | bool) -> bool:
        return val if type(val) == bool else val.lower() in ["true", "yes", "1"]

    def _parse_list(self, val: str) -> list:
        return ast.literal_eval(val)

    def _parse_dict(self, val: str) -> dict:
        return ast.literal_eval(val)

    def _parse_str(self, val: str) -> str | None:
        if str(val).lower() in ["none", "null"]:
            return None
        return val

    def __repr__(self):
        return str(self.__dict__)
