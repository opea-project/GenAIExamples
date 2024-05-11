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


from comps import RemoteMicroService, ServiceOrchestrator


class MyServiceOrchestrator:
    def __init__(self, port=8000):
        self.service_builder = ServiceOrchestrator(port=port)

    def add_remote_service(self):
        asr = RemoteMicroService(
            name="asr", host="10.165.57.68", port=9099, expose_endpoint="/v1/audio/transcriptions"
        )
        tts = RemoteMicroService(
            name="tts", host="10.165.57.68", port=9999, expose_endpoint="/v1/audio/speech"
        )
        llm = RemoteMicroService(name="llm", host="10.165.57.68", port=9001, expose_endpoint="/v1/chat/completions")
        self.service_builder.add(asr).add(tts).add(llm)
        self.service_builder.flow_to(asr, llm)
        self.service_builder.flow_to(llm, tts)

    def schedule(self):
        self.service_builder.schedule(initial_inputs={"url": "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample_2.wav"})
        self.service_builder.get_all_final_outputs()
        result_dict = self.service_builder.result_dict
        # print(result_dict.keys())


if __name__ == "__main__":
    service_ochestrator = MyServiceOrchestrator(port=9001)
    service_ochestrator.add_remote_service()
    service_ochestrator.schedule()