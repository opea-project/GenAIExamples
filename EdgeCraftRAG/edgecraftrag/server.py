# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import uvicorn
from edgecraftrag.api.v1.agent import agent_app, restore_agent_configurations
from edgecraftrag.api.v1.chatqna import chatqna_app
from edgecraftrag.api.v1.data import data_app
from edgecraftrag.api.v1.knowledge_base import kb_app, restore_knowledge_configurations
from edgecraftrag.api.v1.model import model_app
from edgecraftrag.api.v1.pipeline import pipeline_app, restore_pipeline_configurations
from edgecraftrag.api.v1.prompt import prompt_app
from edgecraftrag.api.v1.session import session_app
from edgecraftrag.api.v1.system import system_app
from edgecraftrag.env import UI_DIRECTORY
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from llama_index.core.settings import Settings


async def lifespan(app: FastAPI):
    try:
        print("Restore pipeline configuration and knowledge base configuration...")
        await restore_pipeline_configurations()
        await restore_knowledge_configurations()
        await restore_agent_configurations()
    except Exception as e:
        pass
    finally:
        yield


app = FastAPI(lifespan=lifespan)
app.mount(UI_DIRECTORY, StaticFiles(directory=UI_DIRECTORY), name=UI_DIRECTORY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


sub_apps = [
    data_app,
    model_app,
    pipeline_app,
    chatqna_app,
    system_app,
    prompt_app,
    kb_app,
    agent_app,
    session_app,
]
for sub_app in sub_apps:
    for route in sub_app.routes:
        app.router.routes.append(route)


if __name__ == "__main__":
    Settings.llm = None

    host = os.getenv("PIPELINE_SERVICE_HOST_IP", "0.0.0.0")
    port = int(os.getenv("PIPELINE_SERVICE_PORT", 16010))
    uvicorn.run(app, host=host, port=port)
