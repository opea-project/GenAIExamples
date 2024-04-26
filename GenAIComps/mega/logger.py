# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import logging
from typing import Callable


class CustomLogger:
    """A custom logger class that adds additional logging levels."""

    def __init__(self, name: str = None):
        """Initialize the logger with a name and custom levels."""
        name = "GenAIComps" if not name else name
        self.logger = logging.getLogger(name)

        # Define custom log levels
        log_config = {
            "DEBUG": 10,
            "INFO": 20,
            "TRAIN": 21,
            "EVAL": 22,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
            "EXCEPTION": 100,
        }

        # Add custom levels to logger
        for key, level in log_config.items():
            logging.addLevelName(level, key)
            if key == "EXCEPTION":
                self.__dict__[key.lower()] = self.logger.exception
            else:
                self.__dict__[key.lower()] = functools.partial(self.log_message, level)

        # Set up log format and handler
        self.format = logging.Formatter(fmt="[%(asctime)-15s] [%(levelname)8s] - %(message)s")
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(self.format)

        # Add handler to logger and set log level
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def log_message(self, log_level: str, msg: str):
        """Log a message at a given level.

        :param log_level: The level at which to log the message.
        :param msg: The message to log.
        """
        self.logger.log(log_level, msg)

    # Define type hints for pylint check
    debug: Callable[[str], None]
    info: Callable[[str], None]
    train: Callable[[str], None]
    eval: Callable[[str], None]
    warning: Callable[[str], None]
    error: Callable[[str], None]
    critical: Callable[[str], None]
    exception: Callable[[str], None]


logger = CustomLogger()
