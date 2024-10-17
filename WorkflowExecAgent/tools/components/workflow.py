# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
from typing import Dict

from tools.components.component import Component


class Workflow(Component):
    """Class for handling EasyData workflow operations.

    Attributes:
        workflow_id: workflow id
        wf_key: workflow key. Generated and stored when starting a servable workflow.
    """

    def __init__(self, request_handler, workflow_id=None, workflow_key=None):
        super().__init__(request_handler)
        self.workflow_id = workflow_id
        self.wf_key = workflow_key

    def start(self, params: Dict[str, str]) -> Dict[str, str]:
        """
        ``POST https://SDK_BASE_URL/serving/servable_workflows/{workflow_id}/start``

        Starts a workflow instance with the workflow_id and parameters provided.
        Returns a workflow key used to track the workflow instance.

        :param dict params: Workflow parameters used to start workflow.

        :returns: WorkflowKey

        :rtype: string
        """
        data = json.dumps({"params": params})
        endpoint = f"serving/servable_workflows/{self.workflow_id}/start"
        self.wf_key = self._make_request(endpoint, "POST", data)["wf_key"]
        if self.wf_key:
            return f"Workflow successfully started. The workflow key is {self.wf_key}."
        else:
            return "Workflow failed to start"

    def get_status(self) -> Dict[str, str]:
        """
        ``GET https://SDK_BASE_URL/serving/serving_workflows/{workflow_key}/status``

        Gets the workflow status.

        :returns: WorkflowStatus

        :rtype: string
        """

        endpoint = f"serving/serving_workflows/{self.wf_key}/status"
        return self._make_request(endpoint, "GET")

    def result(self) -> list[Dict[str, str]]:
        """
        ``GET https://SDK_BASE_URL/serving/serving_workflows/{workflow_key}/results``

        Gets the workflow output result.

        :returns: WorkflowOutputData

        :rtype: string
        """

        endpoint = f"serving/serving_workflows/{self.wf_key}/results"
        return self._make_request(endpoint, "GET")
