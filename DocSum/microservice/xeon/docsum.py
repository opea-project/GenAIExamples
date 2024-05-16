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


class MyServiceOrchestrator:
    def __init__(self, port=8000):
        self.service_builder = ServiceOrchestrator(port=port)

    def add_remote_service(self):
        llm = MicroService(name="llm", host="0.0.0.0", port=9000, expose_endpoint="/v1/chat/docsum")
        self.service_builder.add(llm)

    def schedule(self):
        self.service_builder.schedule(
            initial_inputs={"text":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}
        )
        self.service_builder.get_all_final_outputs()
        result_dict = self.service_builder.result_dict
        print(result_dict)


if __name__ == "__main__":
    service_ochestrator = MyServiceOrchestrator(port=9001)
    service_ochestrator.add_remote_service()
    service_ochestrator.schedule()