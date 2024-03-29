#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import sys
from queue import Queue
from threading import Thread

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import StreamingResponse
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.globals import set_debug
from langchain.retrievers.web_research import WebResearchRetriever
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.llms import HuggingFaceEndpoint
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.vectorstores import Chroma
from starlette.middleware.cors import CORSMiddleware

set_debug(True)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TGI_ENDPOINT = os.getenv("TGI_ENDPOINT", "http://localhost:8080")
SHOW_INTERMEDIATE_LOG = os.getenv("SHOW_INTERMEDIATE_LOG", "True").lower() in ("true", "1")


class QueueCallbackHandler(BaseCallbackHandler):
    """A queue that holds the result answer token buffer for streaming response."""

    def __init__(self, queue: Queue):
        self.queue = queue
        self.enter_answer_phase = False

    def on_llm_new_token(self, token: str, **kwargs):
        sys.stdout.write(token)
        sys.stdout.flush()
        if SHOW_INTERMEDIATE_LOG or self.enter_answer_phase:
            self.queue.put(
                {
                    "answer": token,
                }
            )

    def on_llm_start(self, *args, **kwargs):
        if SHOW_INTERMEDIATE_LOG:
            if not self.enter_answer_phase:
                msg = "The search engine begin to fetch the HTML pages with these questions:"
            else:
                msg = "\nGet the answer from Large Language Models:\n"
            self.queue.put(
                {
                    "answer": msg,
                }
            )

    def on_llm_end(self, *args, **kwargs):
        self.enter_answer_phase = not self.enter_answer_phase
        return True


class SearchQuestionAnsweringAPIRouter(APIRouter):
    """The router for SearchQnA example.

    The input request will firstly go through Google Search, and the fetched HTML will be stored in the vector db.
    Then the input request together with relevant retrieved documents will be forward to the LLM to get the answers.
    """

    def __init__(
        self,
        entrypoint: str,
        vectordb_embedding_model: str = "hkunlp/instructor-large",
        vectordb_persistent_directory: str = "/home/user/chroma_db_oai",
    ) -> None:
        super().__init__()
        self.entrypoint = entrypoint
        self.queue = Queue()  # For streaming output tokens

        # setup TGI endpoint
        self.llm = HuggingFaceEndpoint(
            endpoint_url=entrypoint,
            max_new_tokens=1024,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=True,
            callbacks=[QueueCallbackHandler(queue=self.queue)],
        )

        # Check that google api key is provided
        if "GOOGLE_API_KEY" not in os.environ or "GOOGLE_API_KEY" not in os.environ:
            raise Exception("Please make sure to set GOOGLE_API_KEY and GOOGLE_API_KEY environment variables!")

        # Clear the last time searching history, which is useful to avoid interfering with current retrievals
        if os.path.exists(vectordb_persistent_directory) and os.path.isdir(vectordb_persistent_directory):
            shutil.rmtree(vectordb_persistent_directory)
        self.vectorstore = Chroma(
            embedding_function=HuggingFaceInstructEmbeddings(model_name=vectordb_embedding_model),
            persist_directory=vectordb_persistent_directory,
        )

        # Build up the google search service
        self.search = GoogleSearchAPIWrapper()

        # Compose the websearch retriever
        self.web_search_retriever = WebResearchRetriever.from_llm(
            vectorstore=self.vectorstore,
            llm=self.llm,
            search=self.search,
            # num_search_results=3
        )

        # Compose the whole chain
        self.llm_chain = RetrievalQAWithSourcesChain.from_chain_type(
            self.llm,
            retriever=self.web_search_retriever,
        )

    def handle_search_chat(self, query: str):
        try:
            response = self.llm_chain({"question": query})
        except Exception as e:
            print(f"LLM chain error: {e}")
            return "Internal Server Error", ""
        return response["answer"], response["sources"]


router = SearchQuestionAnsweringAPIRouter(
    entrypoint=TGI_ENDPOINT,
)


@router.post("/v1/rag/web_search_chat")
async def web_search_chat(request: Request):
    params = await request.json()
    print(f"[websearch - chat] POST request: /v1/rag/web_search_chat, params:{params}")
    query = params["query"]
    answer, sources = router.handle_search_chat(query={"question": query})
    print(f"[websearch - chat] answer: {answer}, sources: {sources}")
    return {"answer": answer, "sources": sources}


@router.post("/v1/rag/web_search_chat_stream")
async def web_search_chat_stream(request: Request):
    params = await request.json()
    print(f"[websearch - streaming chat] POST request: /v1/rag/web_search_chat_stream, params:{params}")
    query = params["query"]

    def stream_callback(query):
        finished = object()

        def task():
            try:
                _ = router.llm_chain({"question": query})
                router.queue.put(finished)
            except Exception as e:
                print(f"LLM chain error: {e}")
                router.queue.put({"answer": "\nInternal Server Error\n"})
                router.queue.put(finished)

        t = Thread(target=task)
        t.start()
        while True:
            try:
                item = router.queue.get()
                if item is finished:
                    break
                yield item
            except Queue.Empty:
                continue

    def stream_generator():
        import codecs

        chat_response = ""
        for res_dict in stream_callback(query={"question": query}):
            text = res_dict["answer"]
            chat_response += text
            if text == " ":
                yield "data: @#$\n\n"
                continue
            # if text.isspace():
            #     continue
            if "\n" in text or "\r" in text:
                text = text.replace("\n", "<br/>").replace(" ", "@#$")
                yield f"data: {text}\n\n"
                continue
            text = text.replace(" ", "@#$")
            yield f"data: {text}\n\n"
        chat_response = chat_response.split("</s>")[0]
        print(f"\n\n[rag - chat_stream] stream response: {chat_response}\n\n")
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    fastapi_port = os.getenv("FASTAPI_PORT", "8000")
    uvicorn.run(app, host="0.0.0.0", port=int(fastapi_port))
