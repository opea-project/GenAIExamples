# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import re

from comps import GraphragGateway, MicroService, ServiceOrchestrator, ServiceType
from langchain_core.prompts import PromptTemplate


class ChatTemplate:
    @staticmethod
    def generate_rag_prompt(question, documents):
        context_str = "\n".join(documents)
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
Please combine the following intermediate answers into a final, conscise and coherent response. \
refer to the search results obtained from the local knowledge base. \
If you don't know the answer to a question, please don't share false information. \n
### Intermediate answers: {context} \n
### Question: {question} \n
### Answer:
"""
        return template.format(context=context_str, question=question)


MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
RETRIEVER_SERVICE_HOST_IP = os.getenv("RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
RETRIEVER_SERVICE_PORT = int(os.getenv("RETRIEVER_SERVICE_PORT", 7000))
LLM_SERVER_HOST_IP = os.getenv("LLM_SERVER_HOST_IP", "0.0.0.0")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 80))


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.RETRIEVER:
        print("make no changes for retriever inputs. AlreadyCheckCompletionRequest")
    elif self.services[cur_node].service_type == ServiceType.LLM:
        # convert TGI/vLLM to unified OpenAI /v1/chat/completions format
        next_inputs = {}
        next_inputs["model"] = "tgi"  # specifically clarify the fake model to make the format unified
        next_inputs["messages"] = [{"role": "user", "content": inputs["inputs"]}]
        next_inputs["max_tokens"] = llm_parameters_dict["max_tokens"]
        next_inputs["top_p"] = llm_parameters_dict["top_p"]
        next_inputs["stream"] = inputs["streaming"]
        next_inputs["frequency_penalty"] = inputs["frequency_penalty"]
        # next_inputs["presence_penalty"] = inputs["presence_penalty"]
        # next_inputs["repetition_penalty"] = inputs["repetition_penalty"]
        next_inputs["temperature"] = inputs["temperature"]
        inputs = next_inputs
    print("inputs after align:\n", inputs)
    return inputs


def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    next_data = {}
    if self.services[cur_node].service_type == ServiceType.RETRIEVER:
        docs = [doc["text"] for doc in data["retrieved_docs"]]
        # handle template
        # if user provides template, then format the prompt with it
        # otherwise, use the default template
        print("outputs before align:\n", inputs)
        if isinstance(inputs.messages, str):
            prompt = inputs.messages
        else:
            prompt = inputs.messages[0]["content"]
        chat_template = llm_parameters_dict["chat_template"]
        if chat_template:
            prompt_template = PromptTemplate.from_template(chat_template)
            input_variables = prompt_template.input_variables
            if sorted(input_variables) == ["context", "question"]:
                prompt = prompt_template.format(question=prompt, context="\n".join(docs))
            elif input_variables == ["question"]:
                prompt = prompt_template.format(question=prompt)
            else:
                print(f"{prompt_template} not used, we only support 2 input variables ['question', 'context']")
                prompt = ChatTemplate.generate_rag_prompt(prompt, docs)
        else:
            print("no rerank no chat template")
            prompt = ChatTemplate.generate_rag_prompt(prompt, docs)

        next_data["inputs"] = prompt
    else:
        next_data = data

    return next_data


def align_generator(self, gen, **kwargs):
    # openai reaponse format
    # b'data:{"id":"","object":"text_completion","created":1725530204,"model":"meta-llama/Meta-Llama-3-8B-Instruct","system_fingerprint":"2.0.1-native","choices":[{"index":0,"delta":{"role":"assistant","content":"?"},"logprobs":null,"finish_reason":null}]}\n\n'
    print("generator in align generator:\n", gen)
    for line in gen:
        line = line.decode("utf-8")
        start = line.find("{")
        end = line.rfind("}") + 1

        json_str = line[start:end]
        try:
            # sometimes yield empty chunk, do a fallback here
            json_data = json.loads(json_str)
            if json_data["choices"][0]["finish_reason"] != "eos_token":
                yield f"data: {repr(json_data['choices'][0]['delta']['content'].encode('utf-8'))}\n\n"
        except Exception as e:
            yield f"data: {repr(json_str.encode('utf-8'))}\n\n"
    yield "data: [DONE]\n\n"


class GraphRAGService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        ServiceOrchestrator.align_generator = align_generator
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVICE_HOST_IP,
            port=RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )

        llm = MicroService(
            name="llm",
            host=LLM_SERVER_HOST_IP,
            port=LLM_SERVER_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(retriever).add(llm)
        self.megaservice.flow_to(retriever, llm)
        self.gateway = GraphragGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    graphrag = GraphRAGService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    graphrag.add_remote_service()
