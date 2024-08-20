# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Copyright 2024 MOSEC Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import re
import time

import requests
from langchain_core.prompts import ChatPromptTemplate

from comps import (
    CustomLogger,
    LLMParamsDoc,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("reranking_mosec_xeon")
logflag = os.getenv("LOGFLAG", False)


@register_microservice(
    name="opea_service@reranking_mosec_xeon",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=LLMParamsDoc,
)
@register_statistics(names=["opea_service@reranking_mosec_xeon"])
def reranking(input: SearchedDoc) -> LLMParamsDoc:
    if logflag:
        logger.info("reranking input: ", input)
    start = time.time()
    if input.retrieved_docs:
        docs = [doc.text for doc in input.retrieved_docs]
        url = mosec_reranking_endpoint + "/inference"
        data = {"query": input.initial_query, "texts": docs}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response_data = response.json()
        best_response = max(response_data, key=lambda response: response["score"])
        doc = input.retrieved_docs[best_response["index"]]
        if doc.text and len(re.findall("[\u4E00-\u9FFF]", doc.text)) / len(doc.text) >= 0.3:
            # chinese context
            template = "仅基于以下背景回答问题:\n{context}\n问题: {question}"
        else:
            template = """Answer the question based only on the following context:
    {context}
    Question: {question}
            """
        prompt = ChatPromptTemplate.from_template(template)
        final_prompt = prompt.format(context=doc.text, question=input.initial_query)
        statistics_dict["opea_service@reranking_mosec_xeon"].append_latency(time.time() - start, None)
        if logflag:
            logger.info(final_prompt.strip())
        return LLMParamsDoc(query=final_prompt.strip())
    else:
        if logflag:
            logger.info(input.initial_query)
        return LLMParamsDoc(query=input.initial_query)


if __name__ == "__main__":
    mosec_reranking_endpoint = os.getenv("MOSEC_RERANKING_ENDPOINT", "http://localhost:8080")
    opea_microservices["opea_service@reranking_mosec_xeon"].start()
