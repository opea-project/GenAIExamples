# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os

from comps import CodeTransGateway, MicroService, ServiceOrchestrator

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")
MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 7777)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)


class CodeTransService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
        )
        self.megaservice.add(llm)
        self.gateway = CodeTransGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)

    async def schedule(self):
        await self.megaservice.schedule(
            initial_inputs={
                "text": """
    ### System: Please translate the following Golang codes into  Python codes.

    ### Original codes:
    '''Golang

    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n

    '''

    ### Translated codes:
"""
            }
        )
        result_dict = self.megaservice.result_dict
        print(result_dict)


if __name__ == "__main__":
    service_ochestrator = CodeTransService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    service_ochestrator.add_remote_service()
    asyncio.run(service_ochestrator.schedule())
