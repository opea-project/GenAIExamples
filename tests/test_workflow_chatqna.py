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
import json
import os
from typing import Union

import requests
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.llms import HuggingFaceEndpoint
from langchain_community.vectorstores import Redis
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from comps import (
    INDEX_NAME,
    INDEX_SCHEMA,
    REDIS_URL,
    EmbedDoc768,
    GeneratedDoc,
    LLMParamsDoc,
    RerankedDoc,
    SearchedDoc,
    ServiceOrchestrator,
    TextDoc,
    opea_microservices,
    register_microservice,
)

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT", "http://localhost:8080")
tei_reranking_endpoint = os.getenv("TEI_RERANKING_ENDPOINT", "http://localhost:8080")
embeddings = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)


@register_microservice(
    name="opea_service@embedding_tgi_gaudi",
    endpoint="/v1/embeddings",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc768,
)
def embedding(input: TextDoc) -> EmbedDoc768:
    embed_vector = embeddings.embed_query(input.text)
    embed_vector = embed_vector[:768]  # Keep only the first 768 elements
    res = EmbedDoc768(text=input.text, embedding=embed_vector)
    return res


opea_microservices["opea_service@embedding_tgi_gaudi"].start()


@register_microservice(name="opea_service@retriever_redis", endpoint="/v1/retrieval", port=7000)
def retrieve(input: EmbedDoc768) -> SearchedDoc:
    embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    vector_db = Redis.from_existing_index(
        embedding=embeddings,
        index_name=INDEX_NAME,
        redis_url=REDIS_URL,
        schema=INDEX_SCHEMA,
    )
    search_res = vector_db.similarity_search_by_vector(embedding=input.embedding)
    searched_docs = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    return result


opea_microservices["opea_service@retriever_redis"].start()


@register_microservice(
    name="opea_service@reranking_tgi_gaudi",
    endpoint="/v1/reranking",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=RerankedDoc,
)
def reranking(input: SearchedDoc) -> RerankedDoc:
    docs = [doc.text for doc in input.retrieved_docs]
    url = tei_reranking_endpoint + "/rerank"
    data = {"query": input.initial_query, "texts": docs}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    response_data = response.json()
    best_response = max(response_data, key=lambda response: response["score"])
    res = RerankedDoc(query=input.initial_query, doc=input.retrieved_docs[best_response["index"]])
    return res


opea_microservices["opea_service@reranking_tgi_gaudi"].start()


@register_microservice(name="opea_service@llm_tgi_gaudi", endpoint="/v1/chat/completions", port=9000)
def llm_generate(input: Union[TextDoc, RerankedDoc]) -> GeneratedDoc:
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
    params = LLMParamsDoc()
    llm = HuggingFaceEndpoint(
        endpoint_url=llm_endpoint,
        max_new_tokens=params.max_new_tokens,
        top_k=params.top_k,
        top_p=params.top_p,
        typical_p=params.typical_p,
        temperature=params.temperature,
        repetition_penalty=params.repetition_penalty,
        streaming=params.streaming,
    )
    if isinstance(input, RerankedDoc):
        template = """Answer the question based only on the following context:
        {context}

        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"question": input.query, "context": input.doc.text})
    elif isinstance(input, TextDoc):
        response = llm.invoke(input.text)
    else:
        raise TypeError("Invalid input type. Expected TextDoc or RerankedDoc.")
    res = GeneratedDoc(text=response, prompt=input.query)
    return res


opea_microservices["opea_service@llm_tgi_gaudi"].start()


if __name__ == "__main__":
    service_builder = ServiceOrchestrator()
    service_builder.add(opea_microservices["opea_service@embedding_tgi_gaudi"]).add(
        opea_microservices["opea_service@retriever_redis"]
    ).add(opea_microservices["opea_service@reranking_tgi_gaudi"]).add(opea_microservices["opea_service@llm_tgi_gaudi"])
    service_builder.flow_to(
        opea_microservices["opea_service@embedding_tgi_gaudi"], opea_microservices["opea_service@retriever_redis"]
    )
    service_builder.flow_to(
        opea_microservices["opea_service@retriever_redis"], opea_microservices["opea_service@reranking_tgi_gaudi"]
    )
    service_builder.flow_to(
        opea_microservices["opea_service@reranking_tgi_gaudi"], opea_microservices["opea_service@llm_tgi_gaudi"]
    )
    asyncio.run(service_builder.schedule(initial_inputs={"text": "What's the total revenue of Nike in 2023?"}))
