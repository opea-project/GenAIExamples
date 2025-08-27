# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import gc
import os

from edgecraftrag.api_schema import ModelIn
from edgecraftrag.context import ctx
from fastapi import FastAPI, HTTPException, status

model_app = FastAPI()

# Model path in container is set to '/home/user/models'
CONTAINER_MODEL_PATH = "/home/user/models/"


# Search available model weight
@model_app.get(path="/v1/settings/weight/{model_id:path}")
async def get_model_weight(model_id):
    try:
        # Normalize and validate the path
        base_path = os.path.normpath(CONTAINER_MODEL_PATH)
        requested_path = os.path.normpath(os.path.join(CONTAINER_MODEL_PATH, model_id))
        if not requested_path.startswith(base_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid model path")
        return get_available_weights(requested_path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=" GET model weight failed")


# Search available model id
@model_app.get(path="/v1/settings/avail-models/{model_type}")
async def get_model_id(model_type):
    try:
        return get_available_models(model_type)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=" GET model failed")


# GET Models
@model_app.get(path="/v1/settings/models")
async def get_models():
    return ctx.get_model_mgr().get_models()


# GET Model
@model_app.get(path="/v1/settings/models/{model_id:path}")
async def get_model_by_name(model_id):
    return ctx.get_model_mgr().get_model_by_name(model_id)


# POST Model
@model_app.post(path="/v1/settings/models")
async def add_model(request: ModelIn):
    modelmgr = ctx.get_model_mgr()
    # Currently use asyncio.Lock() to deal with multi-requests
    async with modelmgr._lock:
        model = modelmgr.search_model(request)
        if model is None:
            model = modelmgr.load_model(request)
            modelmgr.add(model)
    return model.model_id + " model loaded"


# PATCH Model
@model_app.patch(path="/v1/settings/models/{model_id:path}")
async def update_model(model_id, request: ModelIn):
    # The process of patch model is : 1.delete model 2.create model
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    modelmgr = ctx.get_model_mgr()
    if active_pl and active_pl.model_existed(model_id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Model is being used by active pipeline, unable to update"
        )
    else:
        async with modelmgr._lock:
            if modelmgr.get_model_by_name(model_id) is None:
                # Need to make sure original model still exists before updating model
                # to prevent memory leak in concurrent requests situation
                err_msg = "Model " + model_id + " not exists"
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
            model = modelmgr.search_model(request)
            if model is None:
                modelmgr.del_model_by_name(model_id)
                # Clean up memory occupation
                gc.collect()
                # load new model
                model = modelmgr.load_model(request)
                modelmgr.add(model)
        return model


# DELETE Model
@model_app.delete(path="/v1/settings/models/{model_id:path}")
async def delete_model(model_id):
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if active_pl and active_pl.model_existed(model_id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Model is being used by active pipeline, unable to remove"
        )
    else:
        modelmgr = ctx.get_model_mgr()
        # Currently use asyncio.Lock() to deal with multi-requests
        async with modelmgr._lock:
            response = modelmgr.del_model_by_name(model_id)
            # Clean up memory occupation
            gc.collect()
        return response


def get_available_weights(model_path):
    avail_weights_compression = []
    for _, dirs, _ in os.walk(model_path):
        for dir_name in dirs:
            if "INT4" in dir_name:
                avail_weights_compression.append("INT4")
            if "INT8" in dir_name:
                avail_weights_compression.append("INT8")
            if "FP16" in dir_name:
                avail_weights_compression.append("FP16")
    return avail_weights_compression


def get_available_models(model_type):
    avail_models = []
    if model_type == "vLLM":
        LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")
        avail_models.append(LLM_MODEL)
    elif model_type == "LLM":
        items = os.listdir(CONTAINER_MODEL_PATH)
        for item in items:
            if item == "BAAI":
                continue
            sub_paths = os.listdir(os.path.join(CONTAINER_MODEL_PATH, item))
            if sub_paths and "INT4" not in sub_paths[0] and "INT8" not in sub_paths[0] and "FP16" not in sub_paths[0]:
                for sub_path in sub_paths:
                    avail_models.append(item + "/" + sub_path)
            else:
                avail_models.append(item)
    else:
        for item in os.listdir(CONTAINER_MODEL_PATH + "BAAI"):
            if (model_type == "reranker" and "rerank" in item) or (model_type == "embedding" and "rerank" not in item):
                avail_models.append("BAAI/" + item)

    return avail_models
