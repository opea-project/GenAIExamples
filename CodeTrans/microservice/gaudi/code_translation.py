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
        llm = RemoteMicroService(name="llm", host="0.0.0.0", port=9000, expose_endpoint="/v1/chat/completions")
        self.service_builder.add(llm)

    def schedule(self):
        self.service_builder.schedule(
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
        self.service_builder.get_all_final_outputs()
        result_dict = self.service_builder.result_dict
        print(result_dict)


if __name__ == "__main__":
    service_ochestrator = MyServiceOrchestrator(port=9007)
    service_ochestrator.add_remote_service()
    service_ochestrator.schedule()
