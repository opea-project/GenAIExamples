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


import json
import os

import requests
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from comps import LLMParamsDoc, SearchedDoc, ServiceType, opea_microservices, register_microservice


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
def reranking(input: SearchedDoc) -> LLMParamsDoc:
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
    return LLMParamsDoc(query=final_prompt.strip())


if __name__ == "__main__":
    tei_reranking_endpoint = os.getenv("TEI_RERANKING_ENDPOINT", "http://localhost:8080")
    opea_microservices["opea_service@reranking_tgi_gaudi"].start()
