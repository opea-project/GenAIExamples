# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import heapq
import json
import os
import re
import time

import requests
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
    if input.retrieved_docs:
        docs = [doc.text for doc in input.retrieved_docs]
        url = tei_reranking_endpoint + "/rerank"
        data = {"query": input.initial_query, "texts": docs}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response_data = response.json()
        best_response_list = heapq.nlargest(input.top_n, response_data, key=lambda x: x["score"])
        context_str = ""
        for best_response in best_response_list:
            context_str = context_str + " " + input.retrieved_docs[best_response["index"]].text
        if context_str and len(re.findall("[\u4E00-\u9FFF]", context_str)) / len(context_str) >= 0.3:
            # chinese context
            template = """
### 你将扮演一个乐于助人、尊重他人并诚实的助手，你的目标是帮助用户解答问题。有效地利用来自本地知识库的搜索结果。确保你的回答中只包含相关信息。如果你不确定问题的答案，请避免分享不准确的信息。
### 搜索结果：{context}
### 问题：{question}
### 回答：
"""
        else:
            template = """
### You are a helpful, respectful and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate the information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results: {context} \n
### Question: {question} \n
### Answer:
"""
        final_prompt = template.format(context=context_str, question=input.initial_query)
        statistics_dict["opea_service@reranking_tgi_gaudi"].append_latency(time.time() - start, None)
        return LLMParamsDoc(query=final_prompt.strip())
    else:
        return LLMParamsDoc(query=input.initial_query)


if __name__ == "__main__":
    tei_reranking_endpoint = os.getenv("TEI_RERANKING_ENDPOINT", "http://localhost:8080")
    opea_microservices["opea_service@reranking_tgi_gaudi"].start()
