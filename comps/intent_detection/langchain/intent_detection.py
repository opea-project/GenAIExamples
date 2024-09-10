# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from langchain import LLMChain, PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint
from template import IntentTemplate

from comps import GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice


@register_microservice(
    name="opea_service@llm_intent",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/intent",
    host="0.0.0.0",
    port=9000,
)
def llm_generate(input: LLMParamsDoc):
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
    llm = HuggingFaceEndpoint(
        endpoint_url=llm_endpoint,
        max_new_tokens=input.max_new_tokens,
        top_k=input.top_k,
        top_p=input.top_p,
        typical_p=input.typical_p,
        temperature=input.temperature,
        repetition_penalty=input.repetition_penalty,
        streaming=input.streaming,
        timeout=600,
    )

    prompt_template = 'Please identify the intent of the user query. You may only respond with "chitchat" or \QA" without explanations or engaging in conversation.### User Query: {query}, ### Response: '
    prompt = PromptTemplate(template=prompt_template, input_variables=["query"])

    llm_chain = LLMChain(prompt=prompt, llm=llm)

    response = llm_chain.invoke(input.query)
    response = response["text"]
    print("response", response)
    return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_intent"].start()
