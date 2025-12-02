# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.api.v1.pipeline import save_pipeline_configurations
from edgecraftrag.api_schema import PromptIn
from edgecraftrag.context import ctx
from edgecraftrag.utils import DEFAULT_TEMPLATE
from fastapi import FastAPI, File, HTTPException, UploadFile, status

prompt_app = FastAPI()


# Upload prompt for LLM ChatQnA using file
@prompt_app.post(path="/v1/chatqna/prompt-file")
async def load_prompt_file(file: UploadFile = File(...)):
    try:
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        generator = pl.generator
        if generator:
            content = await file.read()
            prompt_str = content.decode("utf-8")
            generator.set_prompt(prompt_str)
            await save_pipeline_configurations("update", pl)
            return "Set LLM Prompt Successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Update prompt for LLM ChatQnA
@prompt_app.post(path="/v1/chatqna/prompt")
async def load_prompt(request: PromptIn):
    try:
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        generator = pl.generator
        if generator:
            prompt_str = request.prompt
            generator.set_prompt(prompt_str)
            await save_pipeline_configurations("update", pl)
            return "Set LLM Prompt Successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Get prompt of LLM ChatQnA
@prompt_app.get(path="/v1/chatqna/prompt")
async def get_prompt():
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            return generator.original_template
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@prompt_app.get(path="/v1/chatqna/prompt/tagged")
async def get_tagged_prompt():
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            return generator.prompt
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tagged prompt not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@prompt_app.get(path="/v1/chatqna/prompt/default")
async def get_default_prompt():
    return DEFAULT_TEMPLATE


# Reset prompt for LLM ChatQnA
@prompt_app.post(path="/v1/chatqna/prompt/reset")
async def reset_prompt():
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            generator.reset_prompt()
            return "Reset LLM Prompt Successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
