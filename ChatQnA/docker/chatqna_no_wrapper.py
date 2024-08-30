# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import re
from comps import ChatQnAGateway, MicroService, ServiceOrchestrator, ServiceType

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
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate the information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \n
### Search results: {context} \n
### Question: {question} \n
### Answer:
"""
        return template.format(context=context_str, question=question)


MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
# EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
# EMBEDDING_SERVICE_PORT = int(os.getenv("EMBEDDING_SERVICE_PORT", 6000))
# RETRIEVER_SERVICE_HOST_IP = os.getenv("RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
# RETRIEVER_SERVICE_PORT = int(os.getenv("RETRIEVER_SERVICE_PORT", 7000))
# RERANK_SERVICE_HOST_IP = os.getenv("RERANK_SERVICE_HOST_IP", "0.0.0.0")
# RERANK_SERVICE_PORT = int(os.getenv("RERANK_SERVICE_PORT", 8000))
# LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
# LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))
EMBEDDING_SERVER_HOST_IP = os.getenv("EMBEDDING_SERVER_HOST_IP", "0.0.0.0")
EMBEDDING_SERVER_PORT = int(os.getenv("EMBEDDING_SERVER_PORT", 6006))
RETRIEVER_SERVICE_HOST_IP = os.getenv("RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
RETRIEVER_SERVICE_PORT = int(os.getenv("RETRIEVER_SERVICE_PORT", 7000))
RERANK_SERVER_HOST_IP = os.getenv("RERANK_SERVER_HOST_IP", "0.0.0.0")
RERANK_SERVER_PORT = int(os.getenv("RERANK_SERVER_PORT", 8808))
LLM_SERVER_HOST_IP = os.getenv("LLM_SERVER_HOST_IP", "0.0.0.0")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 9009))

def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict):
    if self.services[cur_node].no_wrapper:
        if self.services[cur_node].service_type == ServiceType.EMBEDDING:
            inputs["inputs"] = inputs["text"]
            del inputs["text"]
    return inputs

def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict):
    if self.services[cur_node].no_wrapper:
        next_data = {}
        if self.services[cur_node].service_type == ServiceType.EMBEDDING:
            assert isinstance(data, list)
            next_data = {"text": inputs["inputs"], "embedding": data[0]}
        elif self.services[cur_node].service_type == ServiceType.RETRIEVER:

            docs = [doc["text"] for doc in data["retrieved_docs"]]

            with_rerank = runtime_graph.downstream(cur_node)[0].startswith('rerank')
            if with_rerank and docs:
                # forward to rerank
                # prepare inputs for rerank
                # TODO add top_n
                next_data["query"] = data["initial_query"]
                next_data["texts"] = [doc['text'] for doc in data["retrieved_docs"]]
            else:
                # forward to llm
                if not docs:
                    # delete the rerank from retriever -> rerank -> llm
                    for ds in reversed(runtime_graph.downstream(cur_node)):
                        for nds in runtime_graph.downstream(ds):
                            runtime_graph.add_edge(cur_node, nds)
                        runtime_graph.delete_node_if_exists(ds)

                # prepare inputs for LLM
                next_data["parameters"] = {}
                next_data["parameters"].update(llm_parameters_dict)
                del next_data["parameters"]["id"]
                del next_data["parameters"]["chat_template"]
                del next_data["parameters"]["streaming"]
                prompt = ChatTemplate.generate_rag_prompt(data["initial_query"], docs)
                next_data["inputs"] = prompt

        elif self.services[cur_node].service_type == ServiceType.RERANK:
            # prepare inputs for LLM
            next_data["parameters"] = {}
            next_data["parameters"].update(llm_parameters_dict)
            del next_data["parameters"]["id"]
            del next_data["parameters"]["chat_template"]
            del next_data["parameters"]["streaming"]

            # rerank the inputs with the scores
            # TODO add top_n
            top_n = 1
            docs = inputs["texts"]
            reranked_docs = []
            for best_response in data[:top_n]:
                reranked_docs.append(docs[best_response["index"]])

            prompt = ChatTemplate.generate_rag_prompt(inputs["query"], reranked_docs)
            next_data["inputs"] = prompt

        data = next_data
    return data

class ChatQnAService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):

        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVER_HOST_IP,
            port=EMBEDDING_SERVER_PORT,
            endpoint="/embed",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
            no_wrapper=True,
        )

        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVICE_HOST_IP,
            port=RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
            no_wrapper=True,
        )

        rerank = MicroService(
            name="rerank",
            host=RERANK_SERVER_HOST_IP,
            port=RERANK_SERVER_PORT,
            endpoint="/rerank",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
            no_wrapper=True,
        )

        llm = MicroService(
            name="llm",
            host=LLM_SERVER_HOST_IP,
            port=LLM_SERVER_PORT,
            endpoint="/generate_stream",    # FIXME non-stream case
            use_remote_service=True,
            service_type=ServiceType.LLM,
            no_wrapper=True,
        )
        self.megaservice.add(embedding).add(retriever).add(rerank).add(llm)
        self.megaservice.flow_to(embedding, retriever)
        self.megaservice.flow_to(retriever, rerank)
        self.megaservice.flow_to(rerank, llm)
        self.gateway = ChatQnAGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


    def add_remote_service_without_rerank(self):

        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVER_HOST_IP,
            port=EMBEDDING_SERVER_PORT,
            endpoint="/embed",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
            no_wrapper=True,
        )

        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVICE_HOST_IP,
            port=RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
            no_wrapper=True,
        )

        llm = MicroService(
            name="llm",
            host=LLM_SERVER_HOST_IP,
            port=LLM_SERVER_PORT,
            endpoint="/generate_stream",  # FIXME non-stream case
            use_remote_service=True,
            service_type=ServiceType.LLM,
            no_wrapper=True,
        )
        self.megaservice.add(embedding).add(retriever).add(llm)
        self.megaservice.flow_to(embedding, retriever)
        self.megaservice.flow_to(retriever, llm)
        self.gateway = ChatQnAGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    chatqna = ChatQnAService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    chatqna.add_remote_service()
    # chatqna.add_remote_service_without_rerank()
