# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import gc

from comps import register_microservice
from edgecraftrag.api_schema import ModelIn
from edgecraftrag.context import ctx


# GET Models
@register_microservice(
    name="opea_service@ec_rag", endpoint="/v1/settings/models", host="0.0.0.0", port=16010, methods=["GET"]
)
async def get_models():
    return ctx.get_model_mgr().get_models()


# GET Model
@register_microservice(
    name="opea_service@ec_rag",
    endpoint="/v1/settings/models/{model_id:path}",
    host="0.0.0.0",
    port=16010,
    methods=["GET"],
)
async def get_model_by_name(model_id):
    return ctx.get_model_mgr().get_model_by_name(model_id)


# POST Model
@register_microservice(
    name="opea_service@ec_rag", endpoint="/v1/settings/models", host="0.0.0.0", port=16010, methods=["POST"]
)
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
@register_microservice(
    name="opea_service@ec_rag",
    endpoint="/v1/settings/models/{model_id:path}",
    host="0.0.0.0",
    port=16010,
    methods=["PATCH"],
)
async def update_model(model_id, request: ModelIn):
    # The process of patch model is : 1.delete model 2.create model
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    modelmgr = ctx.get_model_mgr()
    if active_pl and active_pl.model_existed(model_id):
        return "Model is being used by active pipeline, unable to update model"
    else:
        async with modelmgr._lock:
            if modelmgr.get_model_by_name(model_id) is None:
                # Need to make sure original model still exists before updating model
                # to prevent memory leak in concurrent requests situation
                return "Model " + model_id + " not exists"
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
@register_microservice(
    name="opea_service@ec_rag",
    endpoint="/v1/settings/models/{model_id:path}",
    host="0.0.0.0",
    port=16010,
    methods=["DELETE"],
)
async def delete_model(model_id):
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if active_pl and active_pl.model_existed(model_id):
        return "Model is being used by active pipeline, unable to remove"
    else:
        modelmgr = ctx.get_model_mgr()
        # Currently use asyncio.Lock() to deal with multi-requests
        async with modelmgr._lock:
            response = modelmgr.del_model_by_name(model_id)
            # Clean up memory occupation
            gc.collect()
        return response
