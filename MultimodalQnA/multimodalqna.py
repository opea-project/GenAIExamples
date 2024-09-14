# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MicroService, MultimodalQnAGateway, ServiceOrchestrator, ServiceType

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
MM_EMBEDDING_SERVICE_HOST_IP = os.getenv("MM_EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
MM_EMBEDDING_PORT_MICROSERVICE = int(os.getenv("MM_EMBEDDING_PORT_MICROSERVICE", 6000))
MM_RETRIEVER_SERVICE_HOST_IP = os.getenv("MM_RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
MM_RETRIEVER_SERVICE_PORT = int(os.getenv("MM_RETRIEVER_SERVICE_PORT", 7000))
LVM_SERVICE_HOST_IP = os.getenv("LVM_SERVICE_HOST_IP", "0.0.0.0")
LVM_SERVICE_PORT = int(os.getenv("LVM_SERVICE_PORT", 9399))


class MultimodalQnAService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.mmrag_megaservice = ServiceOrchestrator()
        self.lvm_megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        mm_embedding = MicroService(
            name="embedding",
            host=MM_EMBEDDING_SERVICE_HOST_IP,
            port=MM_EMBEDDING_PORT_MICROSERVICE,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )

        mm_retriever = MicroService(
            name="retriever",
            host=MM_RETRIEVER_SERVICE_HOST_IP,
            port=MM_RETRIEVER_SERVICE_PORT,
            endpoint="/v1/multimodal_retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )
        lvm = MicroService(
            name="lvm",
            host=LVM_SERVICE_HOST_IP,
            port=LVM_SERVICE_PORT,
            endpoint="/v1/lvm",
            use_remote_service=True,
            service_type=ServiceType.LVM,
        )

        # for mmrag megaservice
        self.mmrag_megaservice.add(mm_embedding).add(mm_retriever).add(lvm)
        self.mmrag_megaservice.flow_to(mm_embedding, mm_retriever)
        self.mmrag_megaservice.flow_to(mm_retriever, lvm)

        # for lvm megaservice
        self.lvm_megaservice.add(lvm)

        self.gateway = MultimodalQnAGateway(
            multimodal_rag_megaservice=self.mmrag_megaservice,
            lvm_megaservice=self.lvm_megaservice,
            host="0.0.0.0",
            port=self.port,
        )


if __name__ == "__main__":
    mmragwithvideos = MultimodalQnAService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    mmragwithvideos.add_remote_service()
