# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps import GeneratedDoc
from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.api_schema import RagOut
from edgecraftrag.context import ctx
from edgecraftrag.utils import serialize_contexts
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

chatqna_app = FastAPI()


# Retrieval
@chatqna_app.post(path="/v1/retrieval")
async def retrieval(request: ChatCompletionRequest):
    nodeswithscore = ctx.get_pipeline_mgr().run_retrieve(chat_request=request)
    print(nodeswithscore)
    if nodeswithscore is not None:
        ret = []
        for n in nodeswithscore:
            ret.append((n.node.node_id, n.node.text, n.score))
        return ret

    return None


# ChatQnA
@chatqna_app.post(path="/v1/chatqna")
async def chatqna(request: ChatCompletionRequest):
    try:
        request.messages = convert_message(request.messages)
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            request.model = generator.model_id
        if request.stream:
            ret, contexts = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            return ret
        else:
            ret, contexts = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            return str(ret)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# RAGQnA
@chatqna_app.post(path="/v1/ragqna")
async def ragqna(request: ChatCompletionRequest):
    try:
        request.messages = convert_message(request.messages)
        res, contexts = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
        if isinstance(res, GeneratedDoc):
            res = res.text
        elif isinstance(res, StreamingResponse):
            collected_data = []
            async for chunk in res.body_iterator:
                collected_data.append(chunk)
            res = "".join(collected_data)

        serialized_contexts = serialize_contexts(contexts)

        ragout = RagOut(query=request.messages, contexts=serialized_contexts, response=str(res))
        return ragout
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Upload prompt file for LLM ChatQnA
@chatqna_app.post(path="/v1/chatqna/prompt")
async def load_prompt(file: UploadFile = File(...)):
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            content = await file.read()
            prompt_str = content.decode("utf-8")
            generator.set_prompt(prompt_str)
            return "Set LLM Prompt Successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Reset prompt for LLM ChatQnA
@chatqna_app.post(path="/v1/chatqna/prompt/reset")
async def reset_prompt():
    try:
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            generator.reset_prompt()
            return "Reset LLM Prompt Successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def convert_message(messages, history_prompt: str = None):
    messages_list = []
    if isinstance(messages, str):
        str_message = messages
    else:
        str_message = ""
        user_indexs = [i for i, msg in enumerate(messages) if msg.get("role") == "user"]
        last_user_index = user_indexs[-1] if user_indexs else -1

        for idx, message in enumerate(messages):
            msg_role = message["role"]
            if msg_role in ["user", "assistant"]:
                content = message["content"]
                if idx == last_user_index and msg_role == "user":
                    messages_list.append(("system", f"{history_prompt}"))
                if isinstance(content, str):
                    messages_list.append((msg_role, content))
                else:
                    raise ValueError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                     detail="Only text content is supported.")
            else:
                raise ValueError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown role: {msg_role}")

        for role, content in messages_list:
            str_message += f"{role}: {content}\n"
    if len(str_message) > 8192:
        str_message = str_message[-8192:]
    return str_message