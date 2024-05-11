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


from comps import ServiceOrchestratorWithYaml


class MyServiceOrchestrator:
    def __init__(self, yaml_file_path="./audioqna.yaml"):
        self.service_builder = ServiceOrchestratorWithYaml(yaml_file_path)

    def schedule(self):
        self.service_builder.schedule(
            initial_inputs={
                "url": "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample_2.wav"
            }
        )
        self.service_builder.get_all_final_outputs()
        result_dict = self.service_builder.result_dict
        print(result_dict.keys())


if __name__ == "__main__":
    service_ochestrator = MyServiceOrchestrator(yaml_file_path="./audioqna.yaml")
    service_ochestrator.schedule()
