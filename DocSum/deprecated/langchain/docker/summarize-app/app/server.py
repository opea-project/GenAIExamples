#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import os

from fastapi import APIRouter, FastAPI, File, Request, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.llms import HuggingFaceEndpoint
from starlette.middleware.cors import CORSMiddleware
from utils import get_current_beijing_time, read_text_from_file

prompt_template = """Write a concise summary of the following:
{text}
CONCISE SUMMARY:"""
prompt = PromptTemplate.from_template(prompt_template)

refine_template = (
    "Your job is to produce a final summary\n"
    "We have provided an existing summary up to a certain point: {existing_answer}\n"
    "We have the opportunity to refine the existing summary"
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{text}\n"
    "------------\n"
    "Given the new context, refine the original summary in Italian"
    "If the context isn't useful, return the original summary."
)
refine_prompt = PromptTemplate.from_template(refine_template)

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


class DocSummaryAPIRouter(APIRouter):

    def __init__(self, upload_dir, entrypoint) -> None:
        super().__init__()
        self.upload_dir = upload_dir
        self.entrypoint = entrypoint
        print(
            f"[rag - router] Initializing API Router, params:\n \
                    upload_dir={upload_dir}, entrypoint={entrypoint}"
        )

        # Define LLM
        self.llm = HuggingFaceEndpoint(
            endpoint_url=entrypoint,
            max_new_tokens=512,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=True,
        )
        print("[rag - router] LLM initialized.")

        self.llm_chain = load_summarize_chain(llm=self.llm, chain_type="map_reduce")

        print("[rag - router] LLM chain initialized.")
        self.doc_sotre = {}

    def handle_rag_chat(self, query: str):
        response = self.llm_chain.invoke(query)
        result = response["result"].split("</s>")[0].split("\n")[0]
        return result


upload_dir = os.getenv("RAG_UPLOAD_DIR", "./upload_dir")
tgi_endpoint = os.getenv("TGI_ENDPOINT", "http://localhost:8080")
router = DocSummaryAPIRouter(upload_dir, tgi_endpoint)


@router.post("/v1/text_summarize")
async def text_summarize(request: Request):
    params = await request.json()
    print(f"[docsum - text_summarize] POST request: /v1/text_summarize, params:{params}")
    text = params["text"]

    # Split text
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(text)
    # Create multiple documents
    docs = [Document(page_content=t) for t in texts]

    async def stream_generator():
        from langserve.serialization import WellKnownLCSerializer

        _serializer = WellKnownLCSerializer()
        async for chunk in router.llm_chain.astream_log(docs):
            data = _serializer.dumps({"ops": chunk.ops}).decode("utf-8")
            print(f"[docsum - text_summarize] data: {data}")
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.post("/v1/file_summarize")
async def file_summarize(request: Request):
    params = await request.json()
    print(f"[docsum - file_summarize] POST request: /v1/file_summarize, params:{params}")
    doc_id = params["doc_id"]
    text = router.doc_sotre[doc_id]

    async def stream_generator():
        from langserve.serialization import WellKnownLCSerializer

        _serializer = WellKnownLCSerializer()
        async for chunk in router.llm_chain.astream_log(text):
            data = _serializer.dumps({"ops": chunk.ops}).decode("utf-8")
            print(f"[docsum - file_summarize] data: {data}")
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.post("/v1/doc_upload")
async def doc_upload(file: UploadFile = File(...)):
    filename = file.filename
    if "/" in filename:
        filename = filename.split("/")[-1]
    print(f"[docsum - upload] POST request: /v1/doc_upload, filename:{filename}")

    # save file to local path
    cur_time = get_current_beijing_time()
    save_file_name = "/tmp/" + cur_time + "-" + filename
    with open(save_file_name, "wb") as fout:
        content = await file.read()
        fout.write(content)
    print(f"[rag - create] file saved to local path: {save_file_name}")

    doc_id, text = read_text_from_file(file, save_file_name)
    router.doc_sotre[doc_id] = text
    print("[docsum - upload] doc created successfully")

    return {"document_id": doc_id}


app.include_router(router)


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
