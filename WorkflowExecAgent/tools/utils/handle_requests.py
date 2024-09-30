# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from functools import wraps

import requests
from logger import get_logger

logger = get_logger(__name__)


class RequestHandler:
    """Class for handling requests.

    Attributes:
        base_url (string): The url of the API.
        api_key (string): Secret token.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def _make_request(self, endpoint, method="GET", data=None, stream=False):
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        error = ""

        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, data, headers=headers, stream=stream)
        elif method == "PUT":
            response = requests.put(url, data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"error: Invalid HTTP method {method}")

        @self._handle_request
        def check_status(response):
            response.raise_for_status()

        error = check_status(response)

        if error:
            return error

        else:
            try:
                response.json()
                return response.json()
            except:
                return response

    def _handle_request(self, func):
        @wraps(func)
        def decorated(response=None, *args, **kwargs):
            if response is not None:
                try:
                    logger.debug(response)
                    return func(response, *args, **kwargs)

                except requests.exceptions.HTTPError as errh:
                    error = {"error": f"{response.status_code} {response.reason} HTTP Error {errh}"}
                except requests.exceptions.ConnectionError as errc:
                    error = {"error": f"{response.status_code} {response.reason} Connection Error {errc}"}
                except requests.exceptions.Timeout as errt:
                    error = {"error": f"{response.status_code} {response.reason} Timeout Error {errt}"}
                except requests.exceptions.ChunkedEncodingError as errck:
                    error = {"error": f"Invalid chunk encoding: {str(errck)}"}
                except requests.exceptions.RequestException as err:
                    error = {"error": f"{response.status_code} {response.reason} {err}"}
                except Exception as err:
                    logger.debug(response)
                    response = response.json()
                    logger.debug(response)
                    error_msg = f'{response["inner_code"]} {response["friendly_message"]}'
                    error = {"status_code": response["status_code"], "error": error_msg}

                return error

            else:
                try:
                    return func(*args, **kwargs)

                except requests.exceptions.HTTPError as errh:
                    error = {"error": f"HTTP Error {errh}"}
                except requests.exceptions.ConnectionError as errc:
                    error = {"error": f"Connection Error {errc}"}
                except requests.exceptions.Timeout as errt:
                    error = {"error": f"Timeout Error {errt}"}
                except requests.exceptions.ChunkedEncodingError as errck:
                    error = {"error": f"Invalid chunk encoding: {str(errck)}"}
                except requests.exceptions.RequestException as err:
                    error = {"error": err}

                logger.error(f"{error}")

                return error

        return decorated

    def _handle_status_logger(self, val_status):
        if val_status["status"] is False:
            logger.error(val_status["msg"])
