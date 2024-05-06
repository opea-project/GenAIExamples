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

import os

from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from comps import GeneratedDoc, LLMParamsDoc, RerankedDoc, opea_microservices, register_microservice


@register_microservice(name="opea_service@llm_tgi_gaudi", expose_endpoint="/v1/chat/completions", port=9000)
def llm_generate(input: RerankedDoc, params: LLMParamsDoc = None) -> GeneratedDoc:
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
    params = params if params else LLMParamsDoc()
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
    template = """Answer the question based only on the following context:
    {input.doc.text}

    Question: {input.query}
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke(input.query)
    res = GeneratedDoc(text=response, prompt=input.query)
    return res


if __name__ == "__main__":
    opea_microservices["opea_service@llm_tgi_gaudi"].start()
