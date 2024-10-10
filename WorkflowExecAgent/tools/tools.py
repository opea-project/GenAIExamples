# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .sdk import EasyDataSDK


def workflow_scheduler(params, workflow_id: int) -> dict:
    sdk = EasyDataSDK(workflow_id=workflow_id)

    return sdk.workflow.start(params)


def workflow_status_checker(workflow_key: int):
    sdk = EasyDataSDK(wf_key=workflow_key)
    workflow_status = sdk.workflow.get_status()["workflow_status"]

    return workflow_status


def workflow_data_retriever(workflow_key: int) -> str:
    sdk = EasyDataSDK(wf_key=workflow_key)

    return sdk.workflow.result()
