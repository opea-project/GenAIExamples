# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from components.workflow import Workflow
from utils.handle_requests import RequestHandler


class EasyDataSDK:
    def __init__(self, workflow_id=None, workflow_key=None):
        self.workflow = Workflow(
            RequestHandler(os.environ["SDK_BASE_URL"], os.environ["SERVING_TOKEN"]),
            workflow_id=workflow_id,
            wf_key=workflow_key,
        )
