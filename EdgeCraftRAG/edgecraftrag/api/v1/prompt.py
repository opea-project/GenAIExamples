# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.api_schema import PromptIn
from edgecraftrag.context import ctx
from fastapi import FastAPI, File, HTTPException, UploadFile, status

prompt_app = FastAPI()


# Upload prompt for LLM ChatQnA using file
@prompt_app.post(path="/v1/chatqna/prompt-file")
async def load_prompt_file(file: UploadFile = File(...)):
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            content = await file.read()
            prompt_str = content.decode("utf-8")
            generator.set_prompt(prompt_str)
            return "Set LLM Prompt Successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Update prompt for LLM ChatQnA
@prompt_app.post(path="/v1/chatqna/prompt")
async def load_prompt(request: PromptIn):
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            prompt_str = request.prompt
            generator.set_prompt(prompt_str)
            return "Set LLM Prompt Successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Get prompt of LLM ChatQnA
@prompt_app.get(path="/v1/chatqna/prompt")
async def get_prompt():
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            return generator.prompt
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
