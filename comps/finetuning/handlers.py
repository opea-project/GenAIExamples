# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import random
import time
import uuid
from pathlib import Path
from typing import Dict

from fastapi import BackgroundTasks, HTTPException
from pydantic_yaml import parse_yaml_raw_as, to_yaml_file
from ray.job_submission import JobSubmissionClient

from comps import CustomLogger
from comps.cores.proto.api_protocol import (
    FineTuningJob,
    FineTuningJobIDRequest,
    FineTuningJobList,
    FineTuningJobsRequest,
)
from comps.finetuning.llm_on_ray.finetune.finetune_config import FinetuneConfig

logger = CustomLogger("finetuning_handlers")

MODEL_CONFIG_FILE_MAP = {
    "meta-llama/Llama-2-7b-chat-hf": "./models/llama-2-7b-chat-hf.yaml",
    "mistralai/Mistral-7B-v0.1": "./models/mistral-7b-v0.1.yaml",
}

DATASET_BASE_PATH = "datasets"
JOBS_PATH = "jobs"
if not os.path.exists(DATASET_BASE_PATH):
    os.mkdir(DATASET_BASE_PATH)

if not os.path.exists(JOBS_PATH):
    os.mkdir(JOBS_PATH)

FineTuningJobID = str
CHECK_JOB_STATUS_INTERVAL = 5  # Check every 5 secs

global ray_client
ray_client: JobSubmissionClient = None

running_finetuning_jobs: Dict[FineTuningJobID, FineTuningJob] = {}
finetuning_job_to_ray_job: Dict[FineTuningJobID, str] = {}


# Add a background task to periodicly update job status
def update_job_status(job_id: FineTuningJobID):
    while True:
        job_status = ray_client.get_job_status(finetuning_job_to_ray_job[job_id])
        status = str(job_status).lower()
        # Ray status "stopped" is OpenAI status "cancelled"
        status = "cancelled" if status == "stopped" else status

        logger.info(f"Status of job {job_id} is '{status}'")

        running_finetuning_jobs[job_id].status = status
        if status == "finished" or status == "cancelled" or status == "failed":
            break
        time.sleep(CHECK_JOB_STATUS_INTERVAL)


def handle_create_finetuning_jobs(request: FineTuningJobsRequest, background_tasks: BackgroundTasks):
    base_model = request.model
    train_file = request.training_file
    train_file_path = os.path.join(DATASET_BASE_PATH, train_file)

    model_config_file = MODEL_CONFIG_FILE_MAP.get(base_model)
    if not model_config_file:
        raise HTTPException(status_code=404, detail=f"Base model '{base_model}' not supported!")

    if not os.path.exists(train_file_path):
        raise HTTPException(status_code=404, detail=f"Training file '{train_file}' not found!")

    with open(model_config_file) as f:
        finetune_config = parse_yaml_raw_as(FinetuneConfig, f)

    finetune_config.Dataset.train_file = train_file_path

    if request.hyperparameters is not None:
        if request.hyperparameters.epochs != "auto":
            finetune_config.Training.epochs = request.hyperparameters.epochs

        if request.hyperparameters.batch_size != "auto":
            finetune_config.Training.batch_size = request.hyperparameters.batch_size

        if request.hyperparameters.learning_rate_multiplier != "auto":
            finetune_config.Training.learning_rate = request.hyperparameters.learning_rate_multiplier

    if os.getenv("HF_TOKEN", None):
        finetune_config.General.config.use_auth_token = os.getenv("HF_TOKEN", None)

    job = FineTuningJob(
        id=f"ft-job-{uuid.uuid4()}",
        model=base_model,
        created_at=int(time.time()),
        training_file=train_file,
        hyperparameters={
            "n_epochs": finetune_config.Training.epochs,
            "batch_size": finetune_config.Training.batch_size,
            "learning_rate_multiplier": finetune_config.Training.learning_rate,
        },
        status="running",
        seed=random.randint(0, 1000) if request.seed is None else request.seed,
    )
    finetune_config.General.output_dir = os.path.join(JOBS_PATH, job.id)
    if os.getenv("DEVICE", ""):

        logger.info(f"specific device: {os.getenv('DEVICE')}")

        finetune_config.Training.device = os.getenv("DEVICE")

    finetune_config_file = f"{JOBS_PATH}/{job.id}.yaml"
    to_yaml_file(finetune_config_file, finetune_config)

    global ray_client
    ray_client = JobSubmissionClient() if ray_client is None else ray_client

    ray_job_id = ray_client.submit_job(
        # Entrypoint shell command to execute
        entrypoint=f"python finetune_runner.py --config_file {finetune_config_file}",
        # Path to the local directory that contains the script.py file
        runtime_env={"working_dir": "./"},
    )

    logger.info(f"Submitted Ray job: {ray_job_id} ...")

    running_finetuning_jobs[job.id] = job
    finetuning_job_to_ray_job[job.id] = ray_job_id

    background_tasks.add_task(update_job_status, job.id)

    return job


def handle_list_finetuning_jobs():
    finetuning_jobs_list = FineTuningJobList(data=list(running_finetuning_jobs.values()), has_more=False)

    return finetuning_jobs_list


def handle_retrieve_finetuning_job(request: FineTuningJobIDRequest):
    fine_tuning_job_id = request.fine_tuning_job_id

    job = running_finetuning_jobs.get(fine_tuning_job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Fine-tuning job '{fine_tuning_job_id}' not found!")
    return job


def handle_cancel_finetuning_job(request: FineTuningJobIDRequest):
    fine_tuning_job_id = request.fine_tuning_job_id

    ray_job_id = finetuning_job_to_ray_job.get(fine_tuning_job_id)
    if ray_job_id is None:
        raise HTTPException(status_code=404, detail=f"Fine-tuning job '{fine_tuning_job_id}' not found!")

    global ray_client
    ray_client = JobSubmissionClient() if ray_client is None else ray_client
    ray_client.stop_job(ray_job_id)

    job = running_finetuning_jobs.get(fine_tuning_job_id)
    job.status = "cancelled"
    return job


async def save_content_to_local_disk(save_path: str, content):
    save_path = Path(save_path)
    try:
        if isinstance(content, str):
            with open(save_path, "w", encoding="utf-8") as file:
                file.write(content)
        else:
            with save_path.open("wb") as fout:
                content = await content.read()
                fout.write(content)
    except Exception as e:

        logger.info(f"Write file failed. Exception: {e}")

        raise Exception(status_code=500, detail=f"Write file {save_path} failed. Exception: {e}")


def handle_list_finetuning_checkpoints(request: FineTuningJobIDRequest):
    fine_tuning_job_id = request.fine_tuning_job_id

    job = running_finetuning_jobs.get(fine_tuning_job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Fine-tuning job '{fine_tuning_job_id}' not found!")
    output_dir = os.path.join(JOBS_PATH, job.id)
    checkpoints = []
    if os.path.exists(output_dir):
        checkpoints = os.listdir(output_dir)
    return checkpoints
