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

import asyncio
import os

from comps import ChatQnAGateway, MicroService, ServiceOrchestrator, ServiceType

SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "0.0.0.0")


class ChatQnAService:
    def __init__(self, port=8000):
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=SERVICE_HOST_IP,
            port=6000,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        retriever = MicroService(
            name="retriever",
            host=SERVICE_HOST_IP,
            port=7000,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )
        rerank = MicroService(
            name="rerank",
            host=SERVICE_HOST_IP,
            port=8000,
            endpoint="/v1/reranking",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
        )
        llm = MicroService(
            name="llm",
            host=SERVICE_HOST_IP,
            port=9000,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(embedding).add(retriever).add(rerank).add(llm)
        self.megaservice.flow_to(embedding, retriever)
        self.megaservice.flow_to(retriever, rerank)
        self.megaservice.flow_to(rerank, llm)
        self.gateway = ChatQnAGateway(megaservice=self.megaservice, host=SERVICE_HOST_IP, port=self.port)

    async def schedule(self):
        await self.megaservice.schedule(initial_inputs={"text": "What is the revenue of Nike in 2023?"})
        result_dict = self.megaservice.result_dict
        print(result_dict)


if __name__ == "__main__":
    chatqna = ChatQnAService(port=8888)
    chatqna.add_remote_service()
    asyncio.run(chatqna.schedule())
