# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import time

import requests
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from comps import (
    LLMParamsDoc,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@reranking_tgi_gaudi",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=LLMParamsDoc,
)
@traceable(run_type="llm")
@register_statistics(names=["opea_service@reranking_tgi_gaudi"])
def reranking(input: SearchedDoc) -> LLMParamsDoc:
    start = time.time()
    docs = [doc.text for doc in input.retrieved_docs]
    url = tei_reranking_endpoint + "/rerank"
    data = {"query": input.initial_query, "texts": docs}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    response_data = response.json()
    best_response = max(response_data, key=lambda response: response["score"])
    template = """Answer the question based only on the following context:
    {context}
    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    doc = input.retrieved_docs[best_response["index"]]
    final_prompt = prompt.format(context=doc.text, question=input.initial_query)
    statistics_dict["opea_service@reranking_tgi_gaudi"].append_latency(time.time() - start, None)
    return LLMParamsDoc(query=final_prompt.strip())


if __name__ == "__main__":
    tei_reranking_endpoint = os.getenv("TEI_RERANKING_ENDPOINT", "http://localhost:8080")
    opea_microservices["opea_service@reranking_tgi_gaudi"].start()
