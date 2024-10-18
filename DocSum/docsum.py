# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os

from comps import DocSumGateway, MicroService, ServiceOrchestrator, ServiceType

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))

DATA_SERVICE_HOST_IP = os.getenv("DATA_SERVICE_HOST_IP", "0.0.0.0")
DATA_SERVICE_PORT = int(os.getenv("DATA_SERVICE_PORT", 7079))

LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))

class DocSumService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        
        data = MicroService(
            name="data",
            host=DATA_SERVICE_HOST_IP,
            port=DATA_SERVICE_PORT,
            endpoint="/v1/docsum/dataprep",
            use_remote_service=True,
            service_type=ServiceType.DATAPREP,
        )
                
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/docsum",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )

        self.megaservice.add(data).add(llm)
        self.megaservice.flow_to(data, llm)                        
        self.gateway = DocSumGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    docsum = DocSumService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    docsum.add_remote_service()
