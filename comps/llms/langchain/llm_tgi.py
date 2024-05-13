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
from typing import Union

from fastapi.responses import StreamingResponse
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from comps import GeneratedDoc, LLMParamsDoc, RerankedDoc, TextDoc, opea_microservices, register_microservice


@register_microservice(name="opea_service@llm_tgi", expose_endpoint="/v1/chat/completions", host="0.0.0.0", port=9000)
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
    final_prompt = None
    if isinstance(input, RerankedDoc):
        template = """Answer the question based only on the following context:
        {context}
        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm | StrOutputParser()
        final_prompt = input.query
        response = chain.invoke({"question": input.query, "context": input.doc.text})
    elif isinstance(input, TextDoc):
        final_prompt = input.text
        response = llm.invoke(input.text)
    else:
        raise TypeError("Invalid input type. Expected TextDoc or RerankedDoc.")
    res = GeneratedDoc(text=response, prompt=final_prompt)
    return res


def post_process_text(text: str):
    if text == " ":
        return "data: @#$\n\n"
    if text == "\n":
        return "data: <br/>\n\n"
    if text.isspace():
        return None
    new_text = text.replace(" ", "@#$")
    return f"data: {new_text}\n\n"


@register_microservice(
    name="opea_service@llm_tgi_stream", expose_endpoint="/v1/chat/completions_stream", host="0.0.0.0", port=9001
)
def llm_generate_stream(input: Union[TextDoc, RerankedDoc]):
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
        final_input = {"question": input.query, "context": input.doc.text}
    elif isinstance(input, TextDoc):
        chain = llm
        final_input = input.text
    else:
        raise TypeError("Invalid input type. Expected TextDoc or RerankedDoc.")

    def stream_generator():
        chat_response = ""
        for text in chain.stream(final_input):
            chat_response += text
            processed_text = post_process_text(text)
            if text and processed_text:
                if "</s>" in text:
                    res = text.split("</s>")[0]
                    if res != "":
                        yield res
                    break
                yield processed_text
        print(f"[llm - chat_stream] stream response: {chat_response}")
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    opea_microservices["opea_service@llm_tgi"].start()
    opea_microservices["opea_service@llm_tgi_stream"].start()
