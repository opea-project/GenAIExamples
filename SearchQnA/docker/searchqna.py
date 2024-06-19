# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MicroService, SearchQnAGateway, ServiceOrchestrator, ServiceType

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 8888)
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
WEB_RETRIEVER_SERVICE_HOST_IP = os.getenv("WEB_RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
WEB_RETRIEVER_SERVICE_PORT = os.getenv("WEB_RETRIEVER_SERVICE_PORT", 7000)
RERANK_SERVICE_HOST_IP = os.getenv("RERANK_SERVICE_HOST_IP", "0.0.0.0")
RERANK_SERVICE_PORT = os.getenv("RERANK_SERVICE_PORT", 8000)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)


class SearchQnAService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        web_retriever = MicroService(
            name="web_retriever",
            host=WEB_RETRIEVER_SERVICE_HOST_IP,
            port=WEB_RETRIEVER_SERVICE_PORT,
            endpoint="/v1/web_retrieval",
            use_remote_service=True,
            service_type=ServiceType.WEB_RETRIEVER,
        )
        rerank = MicroService(
            name="rerank",
            host=RERANK_SERVICE_HOST_IP,
            port=RERANK_SERVICE_PORT,
            endpoint="/v1/reranking",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
        )
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(embedding).add(web_retriever).add(rerank).add(llm)
        self.megaservice.flow_to(embedding, web_retriever)
        self.megaservice.flow_to(web_retriever, rerank)
        self.megaservice.flow_to(rerank, llm)
        self.gateway = SearchQnAGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    searchqna = SearchQnAService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    searchqna.add_remote_service()
