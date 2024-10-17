# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from tools.components.workflow import Workflow
from tools.utils.handle_requests import RequestHandler


class EasyDataSDK:
    def __init__(self):
        self.request_handler = RequestHandler(os.environ["SDK_BASE_URL"], os.environ["SERVING_TOKEN"])

    def create_workflow(self, workflow_id=None, workflow_key=None):
        return Workflow(
            self.request_handler,
            workflow_id=workflow_id,
            workflow_key=workflow_key,
        )
