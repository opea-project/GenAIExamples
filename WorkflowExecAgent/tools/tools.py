# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time

from tools.sdk import EasyDataSDK


def workflow_executor(params, workflow_id: int) -> dict:
    sdk = EasyDataSDK()
    workflow = sdk.create_workflow(workflow_id)

    params = {key: str(val) for key, val in params.items()}
    start_workflow = workflow.start(params)
    print(start_workflow)

    def check_workflow():
        workflow_status = workflow.get_status()["workflow_status"]
        if workflow_status == "finished":
            message = "Workflow finished."
        elif workflow_status == "initializing" or workflow_status == "running":
            message = "Workflow execution is still in progress."
        else:
            message = "Workflow has failed."

        return workflow_status, message

    MAX_RETRY = 50
    num_retry = 0
    while num_retry < MAX_RETRY:
        workflow_status, message = check_workflow()
        print(message)
        if workflow_status == "failed" or workflow_status == "finished":
            break
        else:
            time.sleep(100)  # interval between each status checking retry
            num_retry += 1

    if workflow_status == "finished":
        return workflow.result()
    else:
        return message
