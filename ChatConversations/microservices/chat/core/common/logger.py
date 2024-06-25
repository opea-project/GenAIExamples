# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

﻿from pydantic import BaseModel
from conf.config import Settings

settings = Settings()


class Logger(BaseModel):
    """Logging configuration to be set for the server.

    Args:
        BaseModel (_type_): _description_
    """

    LOGGER_NAME: str = settings.APP_NAME
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(funcName)s | {%(pathname)s:%(lineno)d} | %(message)s"
    LOG_LEVEL: str = "DEBUG"
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: dict = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }
