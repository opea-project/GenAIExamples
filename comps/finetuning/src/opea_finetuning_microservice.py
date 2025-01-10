# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import os

from fastapi import BackgroundTasks, Depends

from comps import CustomLogger, opea_microservices, register_microservice
from comps.cores.proto.api_protocol import FineTuningJobIDRequest, UploadFileRequest
from comps.finetuning.src.integrations.finetune_config import FineTuningParams
from comps.finetuning.src.integrations.native import OpeaFinetuning, upload_file
from comps.finetuning.src.opea_finetuning_loader import OpeaFinetuningLoader

logger = CustomLogger("opea_finetuning_microservice")

finetuning_component_name = os.getenv("FINETUNING_COMPONENT_NAME", "OPEA_FINETUNING")
# Initialize OpeaComponentLoader
loader = OpeaFinetuningLoader(
    finetuning_component_name,
    description=f"OPEA FINETUNING Component: {finetuning_component_name}",
)


@register_microservice(name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs", host="0.0.0.0", port=8015)
def create_finetuning_jobs(request: FineTuningParams, background_tasks: BackgroundTasks):
    return loader.create_finetuning_jobs(request, background_tasks)


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs", host="0.0.0.0", port=8015, methods=["GET"]
)
def list_finetuning_jobs():
    return loader.list_finetuning_jobs()


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs/retrieve", host="0.0.0.0", port=8015
)
def retrieve_finetuning_job(request: FineTuningJobIDRequest):
    job = loader.retrieve_finetuning_job(request)
    return job


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/fine_tuning/jobs/cancel", host="0.0.0.0", port=8015
)
def cancel_finetuning_job(request: FineTuningJobIDRequest):
    job = loader.cancel_finetuning_job(request)
    return job


@register_microservice(
    name="opea_service@finetuning",
    endpoint="/v1/files",
    host="0.0.0.0",
    port=8015,
)
async def upload_training_files(request: UploadFileRequest = Depends(upload_file)):
    uploadFileInfo = await loader.upload_training_files(request)
    return uploadFileInfo


@register_microservice(
    name="opea_service@finetuning", endpoint="/v1/finetune/list_checkpoints", host="0.0.0.0", port=8015
)
def list_checkpoints(request: FineTuningJobIDRequest):
    checkpoints = loader.list_finetuning_checkpoints(request)
    return checkpoints


if __name__ == "__main__":
    opea_microservices["opea_service@finetuning"].start()
