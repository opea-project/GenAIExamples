# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MicroService, ServiceOrchestrator, ServiceType, VisualQnAGateway

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
LVM_SERVICE_HOST_IP = os.getenv("LVM_SERVICE_HOST_IP", "0.0.0.0")
LVM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9399))


class VisualQnAService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        llm = MicroService(
            name="lvm",
            host=LVM_SERVICE_HOST_IP,
            port=LVM_SERVICE_PORT,
            endpoint="/v1/lvm",
            use_remote_service=True,
            service_type=ServiceType.LVM,
        )
        self.megaservice.add(llm)
        self.gateway = VisualQnAGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    visualqna = VisualQnAService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    visualqna.add_remote_service()
