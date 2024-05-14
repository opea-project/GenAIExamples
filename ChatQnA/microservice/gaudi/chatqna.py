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


from comps import MicroService, ServiceOrchestrator


class ChatQnAService:
    def __init__(self, port=8000):
        self.service_builder = ServiceOrchestrator(host="0.0.0.0", port=port, endpoint="/v1/chatqna")

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding", host="0.0.0.0", port=6000, expose_endpoint="/v1/embeddings", use_remote_service=True
        )
        retriever = MicroService(
            name="retriever", host="0.0.0.0", port=7000, expose_endpoint="/v1/retrieval", use_remote_service=True
        )
        rerank = MicroService(
            name="rerank", host="0.0.0.0", port=8000, expose_endpoint="/v1/reranking", use_remote_service=True
        )
        llm = MicroService(
            name="llm", host="0.0.0.0", port=9000, expose_endpoint="/v1/chat/completions", use_remote_service=True
        )
        self.service_builder.add(embedding).add(retriever).add(rerank).add(llm)
        self.service_builder.flow_to(embedding, retriever)
        self.service_builder.flow_to(retriever, rerank)
        self.service_builder.flow_to(rerank, llm)
        self.service_builder.start_server()

    def schedule(self):
        self.service_builder.schedule(initial_inputs={"text": "What is the revenue of Nike in 2023?"})
        self.service_builder.get_all_final_outputs()
        result_dict = self.service_builder.result_dict
        print(result_dict)


if __name__ == "__main__":
    chatqna = ChatQnAService(port=8888)
    chatqna.add_remote_service()
    chatqna.schedule()
