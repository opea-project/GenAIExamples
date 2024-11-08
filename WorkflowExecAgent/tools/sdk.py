# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from tools.components.workflow import Workflow
from tools.utils.handle_requests import RequestHandler


class DataInsightAutomationSDK:  # Example SDK class for Data Insight Automation platform
    """SDK class containing all components.

    Attributes:
        request_handler: RequestHandler object
    """

    def __init__(self):
        self.request_handler = RequestHandler(os.environ["SDK_BASE_URL"], os.environ["SERVING_TOKEN"])

    def create_workflow(self, workflow_id: int = None, workflow_key=None):
        """Creates a Workflow object.

        :param int workflow_id: Servable workflow id.

        :returns: Workflow
        """

        return Workflow(
            self.request_handler,
            workflow_id=workflow_id,
            workflow_key=workflow_key,
        )
