# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import ast
import asyncio
import json
import os
import re
import time

import requests
from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.proto.docarray import LLMParams, RerankerParms, RetrieverParms
from fastapi import Request
from fastapi.responses import StreamingResponse
from langchain_core.prompts import PromptTemplate


class ChatTemplate:
    @staticmethod
    def generate_rag_prompt(question, documents):
        context_str = "\n".join(documents)
        if context_str and len(re.findall("[\u4e00-\u9fff]", context_str)) / len(context_str) >= 0.3:
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
If you don't know the answer to a question, please don't share false information. \n
### Search results: {context} \n
### Question: {question} \n
### Answer:
"""
        return template.format(context=context_str, question=question)

    @staticmethod
    def generate_fuse_prompt(question, unstruct_documents, struct_str):
        unstruct_str = "\n".join(unstruct_documents)
        context_str = f"Structured: {struct_str} Unstructured: {unstruct_str}"
        if context_str and len(re.findall("[\u4e00-\u9fff]", context_str)) / len(context_str) >= 0.3:
            # chinese context
            template = """
您是一位知識豐富的助手，經過訓練來整合結構化和非結構化的信息，以統一的方式回答問題。在答案中不要區分結構化和非結構化的信息。
回答問題: {question}。指示: 僅使用提供的結構化和非結構化檢索結果來回答問題。
{context}
"""
        else:
            template = """
You are a knowledgeable assistant trained to integrate information for both structured and unstructured retrieval results to answer questions in a unified manner. Do not differentiate structured and unstructured information in the answer. Answer the question: {question}. Instructions: Use only the provided structured and unstructured results to answer the question. {context}.
"""
        return template.format(context=context_str, question=question)


MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
EMBEDDING_SERVER_HOST_IP = os.getenv("EMBEDDING_SERVER_HOST_IP", "0.0.0.0")
EMBEDDING_SERVER_PORT = int(os.getenv("EMBEDDING_SERVER_PORT", 80))
RETRIEVER_SERVER_HOST_IP = os.getenv("RETRIEVER_SERVER_HOST_IP", "0.0.0.0")
RETRIEVER_SERVER_PORT = int(os.getenv("RETRIEVER_SERVER_PORT", 7000))
RERANK_SERVER_HOST_IP = os.getenv("RERANK_SERVER_HOST_IP", "0.0.0.0")
RERANK_SERVER_PORT = int(os.getenv("RERANK_SERVER_PORT", 80))
LLM_SERVER_HOST_IP = os.getenv("LLM_SERVER_HOST_IP", "0.0.0.0")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 80))
TEXT2CYPHER_SERVER_HOST_IP = os.getenv("TEXT2CYPHER_SERVER_HOST_IP", "0.0.0.0")
TEXT2CYPHER_SERVER_PORT = int(os.getenv("TEXT2CYPHER_SERVER_PORT", 11801))
REDIS_SERVER_HOST_IP = os.getenv("REDIS_SERVER_HOST_IP", "0.0.0.0")
REDIS_SERVER_PORT = int(os.getenv("REDIS_SERVER_PORT", 6379))
refresh_db = os.getenv("refresh_db", "True")
cypher_insert = os.getenv("cypher_insert", None)

LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        inputs["inputs"] = inputs["text"]
        del inputs["text"]
    elif self.services[cur_node].service_type == ServiceType.RETRIEVER:
        # prepare the retriever params
        retriever_parameters = kwargs.get("retriever_parameters", None)
        if retriever_parameters:
            inputs.update(retriever_parameters.dict())
    elif self.services[cur_node].service_type == ServiceType.LLM:
        # convert TGI/vLLM to unified OpenAI /v1/chat/completions format
        next_inputs = {}
        next_inputs["model"] = LLM_MODEL
        next_inputs["messages"] = [{"role": "user", "content": inputs["inputs"]}]
        next_inputs["max_tokens"] = llm_parameters_dict["max_tokens"]
        next_inputs["top_p"] = llm_parameters_dict["top_p"]
        next_inputs["stream"] = inputs["stream"]
        next_inputs["frequency_penalty"] = inputs["frequency_penalty"]
        next_inputs["temperature"] = inputs["temperature"]
        inputs = next_inputs
    return inputs


def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    next_data = {}
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        assert isinstance(data, list)
        next_data = {"text": inputs["inputs"], "embedding": data[0]}
    elif self.services[cur_node].service_type == ServiceType.RETRIEVER:

        docs = [doc["text"] for doc in data["retrieved_docs"]]

        with_rerank = runtime_graph.downstream(cur_node)[0].startswith("rerank")
        if with_rerank and docs:
            # forward to rerank
            # prepare inputs for rerank
            next_data["query"] = data["initial_query"]
            next_data["texts"] = [doc["text"] for doc in data["retrieved_docs"]]
        else:
            # forward to llm
            if not docs and with_rerank:
                # delete the rerank from retriever -> rerank -> llm
                for ds in reversed(runtime_graph.downstream(cur_node)):
                    for nds in runtime_graph.downstream(ds):
                        runtime_graph.add_edge(cur_node, nds)
                    runtime_graph.delete_node_if_exists(ds)

            # handle template
            # if user provides template, then format the prompt with it
            # otherwise, use the default template
            prompt = data["initial_query"]
            chat_template = llm_parameters_dict["chat_template"]
            if chat_template:
                prompt_template = PromptTemplate.from_template(chat_template)
                input_variables = prompt_template.input_variables
                if sorted(input_variables) == ["context", "question"]:
                    prompt = prompt_template.format(question=data["initial_query"], context="\n".join(docs))
                elif input_variables == ["question"]:
                    prompt = prompt_template.format(question=data["initial_query"])
                else:
                    print(f"{prompt_template} not used, we only support 2 input variables ['question', 'context']")
                    prompt = ChatTemplate.generate_rag_prompt(data["initial_query"], docs)
            else:
                prompt = ChatTemplate.generate_rag_prompt(data["initial_query"], docs)

            next_data["inputs"] = prompt

    elif self.services[cur_node].service_type == ServiceType.RERANK:
        # rerank the inputs with the scores
        reranker_parameters = kwargs.get("reranker_parameters", None)
        prompt = inputs["query"]
        hybridrag = kwargs.get("hybridrag", None)
        # retrieve structured from cache
        timeout = 120  # seconds
        interval = 1  # polling interval in seconds
        elapsed = 0

        retrieved = None
        structured_result = ""
        while elapsed < timeout:
            retrieved = hybridrag.cache
            if retrieved is not None:
                break
            time.sleep(interval)
            elapsed += interval
        if retrieved:
            structured_result = retrieved

            # reset the cache
            hybridrag.cache = None

        top_n = reranker_parameters.top_n if reranker_parameters else 1
        docs = inputs["texts"]
        reranked_docs = []
        for best_response in data[:top_n]:
            reranked_docs.append(docs[best_response["index"]])

        unstruct_str = "\n".join(reranked_docs)
        fused = f"Structured: {structured_result} Unstructured: {unstruct_str}"

        # handle template
        # if user provides template, then format the prompt with it
        # otherwise, use the default template
        chat_template = llm_parameters_dict["chat_template"]
        if chat_template:
            prompt_template = PromptTemplate.from_template(chat_template)
            input_variables = prompt_template.input_variables
            if sorted(input_variables) == ["context", "question"]:
                prompt = prompt_template.format(question=prompt, context=fused)
            elif input_variables == ["question"]:
                prompt = prompt_template.format(question=prompt)
            else:
                print(f"{prompt_template} not used, we only support 2 input variables ['question', 'context']")
                prompt = ChatTemplate.generate_fuse_prompt(prompt, reranked_docs, structured_result)
        else:
            prompt = ChatTemplate.generate_fuse_prompt(prompt, reranked_docs, structured_result)

        next_data["inputs"] = prompt

    elif self.services[cur_node].service_type == ServiceType.LLM and not llm_parameters_dict["stream"]:
        if "faqgen" in self.services[cur_node].endpoint:
            next_data = data
        else:
            next_data["text"] = data["choices"][0]["message"]["content"]
    else:
        next_data = data

    return next_data


def align_generator(self, gen, **kwargs):
    # OpenAI response format
    # b'data:{"id":"","object":"text_completion","created":1725530204,"model":"meta-llama/Meta-Llama-3-8B-Instruct","system_fingerprint":"2.0.1-native","choices":[{"index":0,"delta":{"role":"assistant","content":"?"},"logprobs":null,"finish_reason":null}]}\n\n'
    for line in gen:
        line = line.decode("utf-8")
        start = line.find("{")
        end = line.rfind("}") + 1

        json_str = line[start:end]
        try:
            # sometimes yield empty chunk, do a fallback here
            json_data = json.loads(json_str)
            if "ops" in json_data and "op" in json_data["ops"][0]:
                if "value" in json_data["ops"][0] and isinstance(json_data["ops"][0]["value"], str):
                    yield f"data: {repr(json_data['ops'][0]['value'].encode('utf-8'))}\n\n"
                else:
                    pass
            elif (
                json_data["choices"][0]["finish_reason"] != "eos_token"
                and "content" in json_data["choices"][0]["delta"]
            ):
                yield f"data: {repr(json_data['choices'][0]['delta']['content'].encode('utf-8'))}\n\n"
        except Exception as e:
            yield f"data: {repr(json_str.encode('utf-8'))}\n\n"
    yield "data: [DONE]\n\n"


class HybridRAGService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.cache = None
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        ServiceOrchestrator.align_generator = align_generator
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.HYBRID_RAG)

    async def exec_text2cypher(self, prompt):
        url = f"http://{TEXT2CYPHER_SERVER_HOST_IP}:{TEXT2CYPHER_SERVER_PORT}/v1/text2query"
        headers = {"Content-Type": "application/json"}
        if refresh_db == "False":
            data = {"query": prompt, "options": {"refresh_db": "False"}}
        elif cypher_insert is not None:
            data = {"query": prompt, "options": {"cypher_insert": "'${cypher_insert}'", "refresh_db": "True"}}
        else:
            data = {"query": prompt}
        response = requests.post(url, json=data)
        data = response.json()
        data_str = str(data)
        start_marker = "['"
        end_marker = "']"

        # Find the start and end indices
        start_index = data_str.find(start_marker) + len(start_marker)  # Move past the start marker
        end_index = data_str.find(end_marker, start_index)  # Find the end marker

        # Extract the substring
        substring = data_str[start_index:end_index]

        # Clean up the substring
        structured = ",".join(item.strip().strip("'") for item in substring.split(","))

        # save to cache
        self.cache = structured
        return structured

    def add_remote_service(self):

        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVER_HOST_IP,
            port=EMBEDDING_SERVER_PORT,
            endpoint="/embed",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )

        text2cypher = MicroService(
            name="text2query",
            host=TEXT2CYPHER_SERVER_HOST_IP,
            port=TEXT2CYPHER_SERVER_PORT,
            endpoint="/text2query",
            use_remote_service=True,
            service_type=ServiceType.TEXT2QUERY,
        )

        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVER_HOST_IP,
            port=RETRIEVER_SERVER_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )

        rerank = MicroService(
            name="rerank",
            host=RERANK_SERVER_HOST_IP,
            port=RERANK_SERVER_PORT,
            endpoint="/rerank",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
        )

        llm = MicroService(
            name="llm",
            host=LLM_SERVER_HOST_IP,
            port=LLM_SERVER_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )

        # Add the microservices to the megaservice orchestrator and define the flow
        self.megaservice.add(embedding).add(retriever).add(rerank).add(llm)
        self.megaservice.flow_to(embedding, retriever)
        self.megaservice.flow_to(retriever, rerank)
        self.megaservice.flow_to(rerank, llm)

    async def read_streaming_response(self, response: StreamingResponse):
        """Reads the streaming response from a StreamingResponse object.

        Parameters:
        - self: Reference to the current instance of the class.
        - response: The StreamingResponse object to read from.

        Returns:
        - str: The complete response body as a decoded string.
        """
        body = b""  # Initialize an empty byte string to accumulate the response chunks
        async for chunk in response.body_iterator:
            body += chunk  # Append each chunk to the body
        return body.decode("utf-8")  # Decode the accumulated byte string to a regular string

    async def process_prompt(self, prompt, llm_parameters, retriever_parameters, reranker_parameters):
        # Create tasks for concurrent execution
        exec_task = asyncio.create_task(self.exec_text2cypher(prompt))
        schedule_task = asyncio.create_task(
            self.megaservice.schedule(
                initial_inputs={"text": prompt},
                llm_parameters=llm_parameters,
                retriever_parameters=retriever_parameters,
                reranker_parameters=reranker_parameters,
                hybridrag=self,
            )
        )

        # Wait for both tasks to complete
        structured_result = await exec_task
        result_dict, runtime_graph = await schedule_task

        return result_dict, runtime_graph

    async def handle_request(self, request: Request):
        """Handles the incoming request, processes it through the appropriate microservices,
        and returns the response.

        Parameters:
        - self: Reference to the current instance of the class.
        - request: The incoming request object.

        Returns:
        - ChatCompletionResponse: The response from the LLM microservice.
        """
        # Parse the incoming request data
        data = await request.json()

        # Get the stream option from the request data, default to True if not provided
        stream_opt = data.get("stream", True)

        # Validate and parse the chat request data
        chat_request = ChatCompletionRequest.model_validate(data)  # parse_obj(data)

        # Handle the chat messages to generate the prompt
        prompt = handle_message(chat_request.messages)

        # Define the LLM parameters
        llm_parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 2048,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=stream_opt,
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
            model=chat_request.model if chat_request.model else None,
        )

        # Define the retriever parameters
        retriever_parameters = RetrieverParms(
            search_type=chat_request.search_type if chat_request.search_type else "similarity",
            k=chat_request.k if chat_request.k else 4,
            distance_threshold=chat_request.distance_threshold if chat_request.distance_threshold else None,
            fetch_k=chat_request.fetch_k if chat_request.fetch_k else 20,
            lambda_mult=chat_request.lambda_mult if chat_request.lambda_mult else 0.5,
            score_threshold=chat_request.score_threshold if chat_request.score_threshold else 0.2,
        )

        # Define the reranker parameters
        reranker_parameters = RerankerParms(
            top_n=chat_request.top_n if chat_request.top_n else 1,
        )

        result_dict, runtime_graph = await self.process_prompt(
            prompt, llm_parameters, retriever_parameters, reranker_parameters
        )
        for node, response in result_dict.items():
            if isinstance(response, StreamingResponse):
                return response
        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]["text"]
        choices = []
        usage = UsageInfo()
        choices.append(
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response),
                finish_reason="stop",
            )
        )
        return ChatCompletionResponse(model="hybridrag", choices=choices, usage=usage)

    def start(self):

        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()


if __name__ == "__main__":
    hybridrag = HybridRAGService(port=MEGA_SERVICE_PORT)
    hybridrag.add_remote_service()

    hybridrag.start()
