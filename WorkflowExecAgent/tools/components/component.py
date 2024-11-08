# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class Component:
    """BaseClass for component objects to make API requests.

    Attributes:
        request_handler: RequestHandler object
    """

    def __init__(self, request_handler):
        self.request_handler = request_handler

    def _make_request(self, *args, **kwargs):
        """Uses the request_handler object to make API requests.

        :returns: API response
        """

        return self.request_handler._make_request(*args, **kwargs)
