# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging

from fastapi import APIRouter, FastAPI
from workflow import run_workflow

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI()

router = APIRouter(prefix="/serving", tags=["Workflow Serving"])

app.results = {}


@router.post("/servable_workflows/{wf_id}/start", summary="Start Workflow")
async def start_workflow(wf_id: int, params: dict):
    try:
        app.results = run_workflow(params["params"])
        wf_key = "example_key"
        return {"msg": "ok", "wf_key": wf_key}

    except Exception as e:
        logging.error(e, exc_info=True)
        return {"msg": "error occurred"}


@router.get("/serving_workflows/{wf_key}/status", summary="Get Workflow Status")
async def get_status(wf_key: str):
    try:
        if app.results:
            status = "finished"
        else:
            status = "failed"

        return {"workflow_status": status}
    except Exception as e:
        logging.error(e)
        return {"msg": "error occurred"}


@router.get("/serving_workflows/{wf_key}/results", summary="Get Workflow Results")
async def get_results(wf_key: str):
    try:
        if app.results:
            return app.results
        else:
            return {"msg": "There is an issue while getting results !!"}

    except Exception as e:
        logging.error(e)
        return {"msg": "There is an issue while getting results !!"}


app.include_router(router)
