# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from fastapi import BackgroundTasks, Depends

from comps import opea_microservices, register_microservice
from comps.cores.proto.api_protocol import FineTuningJobIDRequest, UploadFileRequest
from comps.finetuning.finetune_config import FineTuningParams
from comps.finetuning.handlers import (
    handle_cancel_finetuning_job,
    handle_create_finetuning_jobs,
    handle_list_finetuning_checkpoints,
    handle_list_finetuning_jobs,
    handle_retrieve_finetuning_job,
    handle_upload_training_files,
    upload_file,
)


@register_microservice(name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs", host="0.0.0.0", port=8015)
def create_finetuning_jobs(request: FineTuningParams, background_tasks: BackgroundTasks):
    return handle_create_finetuning_jobs(request, background_tasks)


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs", host="0.0.0.0", port=8015, methods=["GET"]
)
def list_finetuning_jobs():
    return handle_list_finetuning_jobs()


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs/retrieve", host="0.0.0.0", port=8015
)
def retrieve_finetuning_job(request: FineTuningJobIDRequest):
    job = handle_retrieve_finetuning_job(request)
    return job


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs/cancel", host="0.0.0.0", port=8015
)
def cancel_finetuning_job(request: FineTuningJobIDRequest):
    job = handle_cancel_finetuning_job(request)
    return job


@register_microservice(
    name="opea_service@finetuning",
    endpoint="/v1/files",
    host="0.0.0.0",
    port=8015,
)
async def upload_training_files(request: UploadFileRequest = Depends(upload_file)):
    uploadFileInfo = await handle_upload_training_files(request)
    return uploadFileInfo


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/finetune/list_checkpoints", host="0.0.0.0", port=8015
)
def list_checkpoints(request: FineTuningJobIDRequest):
    checkpoints = handle_list_finetuning_checkpoints(request)
    return checkpoints


if __name__ == "__main__":
    opea_microservices["opea_service@finetuning"].start()
