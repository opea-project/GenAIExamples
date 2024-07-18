#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import os

from fastapi import APIRouter, FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from guardrails import moderation_prompt_for_chat, unsafe_dict
from langchain.globals import set_debug, set_verbose
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.llms import HuggingFaceEndpoint
from langchain_community.vectorstores import Redis
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langserve import add_routes
from prompts import contextualize_q_prompt, prompt, qa_prompt
from rag_redis.config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, REDIS_URL
from starlette.middleware.cors import CORSMiddleware
from utils import (
    create_kb_folder,
    create_retriever_from_files,
    create_retriever_from_links,
    get_current_beijing_time,
    post_process_text,
    reload_retriever,
)

set_verbose(True)
set_debug(True)


app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


class RAGAPIRouter(APIRouter):

    def __init__(self, upload_dir, entrypoint, safety_guard_endpoint, tei_endpoint=None) -> None:
        super().__init__()
        self.upload_dir = upload_dir
        self.entrypoint = entrypoint
        self.safety_guard_endpoint = safety_guard_endpoint
        print(
            f"[rag - router] Initializing API Router, params:\n \
                    upload_dir={upload_dir}, entrypoint={entrypoint}"
        )

        # Define LLM
        self.llm = HuggingFaceEndpoint(
            endpoint_url=entrypoint,
            max_new_tokens=1024,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=True,
        )
        # for NeuralChatEndpoint:
        """
        self.llm = NeuralChatEndpoint(
            endpoint_url=entrypoint,
            max_new_tokens=1024,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=True,
        )
        """
        if self.safety_guard_endpoint:
            self.llm_guard = HuggingFaceEndpoint(
                endpoint_url=safety_guard_endpoint,
                max_new_tokens=100,
                top_k=1,
                top_p=0.95,
                typical_p=0.95,
                temperature=0.01,
                repetition_penalty=1.03,
            )
        print("[rag - router] LLM initialized.")

        # Define LLM Chain
        if tei_endpoint:
            # create embeddings using TEI endpoint service
            self.embeddings = HuggingFaceHubEmbeddings(model=tei_endpoint)
        else:
            # create embeddings using local embedding model
            self.embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

        try:
            rds = Redis.from_existing_index(
                self.embeddings,
                index_name=INDEX_NAME,
                redis_url=REDIS_URL,
                schema=INDEX_SCHEMA,
            )
            retriever = rds.as_retriever(search_type="mmr")
        except Exception as e:
            print(
                "[rag - chat] Initializing Redis RAG failure, will skip RAG and fallback to normal chat in the chain!"
            )
            retriever = None
        # Define contextualize chain
        # self.contextualize_q_chain = contextualize_q_prompt | self.llm | StrOutputParser()
        self.contextualize_q_chain = prompt | self.llm | StrOutputParser()

        # Define LLM chain
        if retriever:
            self.llm_chain = (
                RunnablePassthrough.assign(context=self.contextualized_question | retriever) | qa_prompt | self.llm
            )
        else:
            self.llm_chain = RunnablePassthrough.assign(context=self.contextualized_question) | prompt | self.llm
        print("[rag - router] LLM chain initialized.")

        # Define chat history
        self.chat_history = []

    def contextualized_question(self, input: dict):
        if input.get("chat_history"):
            return self.contextualize_q_chain
        else:
            return input["question"]

    def handle_rag_chat(self, query: str):
        response = self.llm_chain.invoke({"question": query, "chat_history": self.chat_history})
        # response = self.llm_chain.invoke({"question": query})
        result = response.split("</s>")[0]
        self.chat_history.extend([HumanMessage(content=query), response])
        # output guardrails
        if self.safety_guard_endpoint:
            response_output_guard = self.llm_guard(
                moderation_prompt_for_chat("Agent", f"User: {query}\n Agent: {response}")
            )
            if "unsafe" in response_output_guard:
                policy_violation_level = response_output_guard.split("\n")[1].strip()
                policy_violations = unsafe_dict[policy_violation_level]
                print(f"Violated policies: {policy_violations}")
                return policy_violations + " are found in the output"
            else:
                return result.lstrip()
        return result.lstrip()


upload_dir = os.getenv("RAG_UPLOAD_DIR", "./upload_dir")
tgi_llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
safety_guard_endpoint = os.getenv("SAFETY_GUARD_ENDPOINT")
tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
router = RAGAPIRouter(upload_dir, tgi_llm_endpoint, safety_guard_endpoint, tei_embedding_endpoint)


@router.post("/v1/rag/chat")
async def rag_chat(request: Request):
    params = await request.json()
    print(f"[rag - chat] POST request: /v1/rag/chat, params:{params}")
    query = params["query"]
    kb_id = params.get("knowledge_base_id", "default")
    print(f"[rag - chat] history: {router.chat_history}")

    # prompt guardrails
    if router.safety_guard_endpoint:
        response_input_guard = router.llm_guard(moderation_prompt_for_chat("User", query))
        if "unsafe" in response_input_guard:
            policy_violation_level = response_input_guard.split("\n")[1].strip()
            policy_violations = unsafe_dict[policy_violation_level]
            print(f"Violated policies: {policy_violations}")
            return f"Violated policies: {policy_violations}, please check your input."

    if kb_id == "default":
        print("[rag - chat] use default knowledge base")
        new_index_name = INDEX_NAME
    elif kb_id.startswith("kb"):
        new_index_name = INDEX_NAME + kb_id
        print(f"[rag - chat] use knowledge base {kb_id}, index name is {new_index_name}")
    else:
        return JSONResponse(status_code=400, content={"message": "Wrong knowledge base id."})

    try:
        retriever = reload_retriever(router.embeddings, new_index_name)
        router.llm_chain = (
            RunnablePassthrough.assign(context=router.contextualized_question | retriever) | qa_prompt | router.llm
        )
    except Exception as e:
        print("[rag - chat] Initializing Redis RAG failure, will skip RAG and fallback to normal chat in the chain!")
    return router.handle_rag_chat(query=query)


@router.post("/v1/rag/chat_stream")
async def rag_chat_stream(request: Request):
    params = await request.json()
    print(f"[rag - chat_stream] POST request: /v1/rag/chat_stream, params:{params}")
    query = params["query"]
    kb_id = params.get("knowledge_base_id", "default")
    print(f"[rag - chat_stream] history: {router.chat_history}")

    # prompt guardrails
    if router.safety_guard_endpoint:
        response_input_guard = router.llm_guard(moderation_prompt_for_chat("User", query))
        if "unsafe" in response_input_guard:
            policy_violation_level = response_input_guard.split("\n")[1].strip()
            policy_violations = unsafe_dict[policy_violation_level]
            print(f"Violated policies: {policy_violations}")

            def generate_content():
                content = f"Violated policies: {policy_violations}, please check your input."
                yield f"data: {content}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate_content(), media_type="text/event-stream")

    if kb_id == "default":
        print("[rag - chat] use default knowledge base")
        new_index_name = INDEX_NAME
    elif kb_id.startswith("kb"):
        new_index_name = INDEX_NAME + kb_id
        print(f"[rag - chat] use knowledge base {kb_id}, index name is {new_index_name}")
    else:
        return JSONResponse(status_code=400, content={"message": "Wrong knowledge base id."})

    try:
        retriever = reload_retriever(router.embeddings, new_index_name)
        router.llm_chain = (
            RunnablePassthrough.assign(context=router.contextualized_question | retriever) | qa_prompt | router.llm
        )
    except Exception as e:
        print("[rag - chat] Initializing Redis RAG failure, will skip RAG and fallback to normal chat in the chain!")

    def stream_generator():
        chat_response = ""
        for text in router.llm_chain.stream({"question": query, "chat_history": router.chat_history}):
            # for text in router.llm_chain.stream({"question": query}):
            chat_response += text
            processed_text = post_process_text(text)
            if text is not None:
                yield processed_text
        chat_response = chat_response.split("</s>")[0]
        print(f"[rag - chat_stream] stream response: {chat_response}")
        router.chat_history.extend([HumanMessage(content=query), chat_response])
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.post("/v1/rag/create")
async def rag_create(file: UploadFile = File(...)):
    filename = file.filename
    if "/" in filename:
        filename = filename.split("/")[-1]
    print(f"[rag - create] POST request: /v1/rag/create, filename:{filename}")

    kb_id, user_upload_dir, user_persist_dir = create_kb_folder(router.upload_dir)
    # save file to local path
    cur_time = get_current_beijing_time()
    save_file_name = str(user_upload_dir) + "/" + cur_time + "-" + filename
    with open(save_file_name, "wb") as fout:
        content = await file.read()
        fout.write(content)
    print(f"[rag - create] file saved to local path: {save_file_name}")

    # create new retriever
    try:
        # get retrieval instance and reload db with new knowledge base
        print("[rag - create] starting to create local db...")
        index_name = INDEX_NAME + kb_id
        retriever = create_retriever_from_files(save_file_name, router.embeddings, index_name)
        router.llm_chain = (
            RunnablePassthrough.assign(context=router.contextualized_question | retriever) | qa_prompt | router.llm
        )
        print("[rag - create] kb created successfully")
    except Exception as e:
        print(f"[rag - create] create knowledge base failed! {e}")
        return JSONResponse(status_code=500, content={"message": "Fail to create new knowledge base."})
    return {"knowledge_base_id": kb_id}


@router.post("/v1/rag/upload_link")
async def rag_upload_link(request: Request):
    params = await request.json()
    link_list = params["link_list"]
    print(f"[rag - upload_link] POST request: /v1/rag/upload_link, link list:{link_list}")

    kb_id, user_upload_dir, user_persist_dir = create_kb_folder(router.upload_dir)

    # create new retriever
    try:
        print("[rag - upload_link] starting to create local db...")
        index_name = INDEX_NAME + kb_id
        retriever = create_retriever_from_links(router.embeddings, link_list, index_name)
        router.llm_chain = (
            RunnablePassthrough.assign(context=router.contextualized_question | retriever) | qa_prompt | router.llm
        )
        print("[rag - upload_link] kb created successfully")
    except Exception as e:
        print(f"[rag - upload_link] create knowledge base failed! {e}")
        return JSONResponse(status_code=500, content={"message": "Fail to create new knowledge base."})
    return {"knowledge_base_id": kb_id}


app.include_router(router)


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


add_routes(app, router.llm_chain, path="/rag-redis")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
