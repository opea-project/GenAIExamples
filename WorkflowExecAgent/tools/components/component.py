# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class Component:
    def __init__(self, request_handler):
        self.request_handler = request_handler

    def _make_request(self, *args, **kwargs):
        return self.request_handler._make_request(*args, **kwargs)
