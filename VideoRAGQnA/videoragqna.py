# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MicroService, ServiceOrchestrator, ServiceType, VideoRAGQnAGateway

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = int(os.getenv("EMBEDDING_SERVICE_PORT", 6000))
RETRIEVER_SERVICE_HOST_IP = os.getenv("RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
RETRIEVER_SERVICE_PORT = int(os.getenv("RETRIEVER_SERVICE_PORT", 7000))
RERANK_SERVICE_HOST_IP = os.getenv("RERANK_SERVICE_HOST_IP", "0.0.0.0")
RERANK_SERVICE_PORT = int(os.getenv("RERANK_SERVICE_PORT", 8000))
LVM_SERVICE_HOST_IP = os.getenv("LVM_SERVICE_HOST_IP", "0.0.0.0")
LVM_SERVICE_PORT = int(os.getenv("LVM_SERVICE_PORT", 9000))


class VideoRAGQnAService:
    def __init__(self, host="0.0.0.0", port=8888):
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
        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVICE_HOST_IP,
            port=RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )
        rerank = MicroService(
            name="rerank",
            host=RERANK_SERVICE_HOST_IP,
            port=RERANK_SERVICE_PORT,
            endpoint="/v1/reranking",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
        )
        lvm = MicroService(
            name="lvm",
            host=LVM_SERVICE_HOST_IP,
            port=LVM_SERVICE_PORT,
            endpoint="/v1/lvm",
            use_remote_service=True,
            service_type=ServiceType.LVM,
        )
        self.megaservice.add(embedding).add(retriever).add(rerank).add(lvm)
        self.megaservice.flow_to(embedding, retriever)
        self.megaservice.flow_to(retriever, rerank)
        self.megaservice.flow_to(rerank, lvm)
        self.gateway = VideoRAGQnAGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    videoragqna = VideoRAGQnAService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    videoragqna.add_remote_service()
