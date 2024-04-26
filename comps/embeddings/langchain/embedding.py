# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio

from docarray.base_doc import DocArrayResponse
from http_service import HTTPService
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from comps import EmbedDoc1024, TextDoc


async def setup():
    runtime_args = {
        "title": "test_service",
        "description": "this is a test.",
        "protocol": "http",
        "port": 8099,
        "host": "localhost",
    }
    # breakpoint()
    service = HTTPService(runtime_args=runtime_args, cors=False)
    app = service.app

    @app.post(
        path="/v1/embed",
        response_model=EmbedDoc1024,
        response_class=DocArrayResponse,
        summary="Get the embedded vector of the input text",
        tags=["Debug"],
    )
    def embedding(input: TextDoc) -> EmbedDoc1024:
        embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-large-en-v1.5")
        embed_vector = embeddings.embed_query(input.text)
        res = EmbedDoc1024(text=input.text, embedding=embed_vector)
        return res

    await service.initialize_server()
    await service.execute_server()


asyncio.run(setup())
