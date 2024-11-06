# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.api.v1.data import data_app
from edgecraftrag.api.v1.model import model_app
from edgecraftrag.api.v1.pipeline import pipeline_app
from edgecraftrag.api.v1.chatqna import chatqna_app

from llama_index.core.settings import Settings

import uvicorn
from fastapi import FastAPI
app = FastAPI()

sub_apps = [data_app, model_app, pipeline_app, chatqna_app]
for sub_app in sub_apps:
    for route in sub_app.routes:
        app.router.routes.append(route)


if __name__ == "__main__":
    Settings.llm = None
    
    uvicorn.run(app, host="0.0.0.0", port=16010)