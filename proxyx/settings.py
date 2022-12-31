import os
import pathlib

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

ROOT_DIR = pathlib.Path(__file__).parents[1].resolve()


PROXYX_APP_CONFIG_PATH = os.environ.get("PROXYX_APP_CONFIG_PATH")
config = Config(env_file=PROXYX_APP_CONFIG_PATH)

PROXYX_ROUTING_CONFIG_PATH = config("PROXYX_ROUTING_CONFIG_PATH")

# Starlette config
DEBUG = config("DEBUG", cast=bool, default=False)
LOG_ALL_HEADERS = config("LOG_ALL_HEADERS", cast=bool, default=False)

# CORSMiddleware config
ALLOW_ORIGINS = config("ALLOW_ORIGINS", cast=CommaSeparatedStrings, default=[])
ALLOW_METHODS = config(
    "ALLOW_METHODS", cast=CommaSeparatedStrings, default=["GET"]
)
ALLOW_HEADERS = config("ALLOW_HEADERS", cast=CommaSeparatedStrings, default=[])
ALLOW_CREDENTIALS = config("ALLOW_CREDENTIALS", cast=bool, default=False)
ALLOW_ORIGIN_REGEX = config("ALLOW_ORIGIN_REGEX", default=None)

# TrustedHostMiddleware config
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", cast=CommaSeparatedStrings, default=None
)

# SENTRY
SENTRY_DSN = config("SENTRY_DSN", default=None)

HIDE_ERROR_MESSAGE = config("HIDE_ERROR_MESSAGE", cast=bool, default=False)
