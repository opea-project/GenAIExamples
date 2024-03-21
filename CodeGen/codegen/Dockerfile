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

FROM langchain/langchain
RUN apt-get update && apt-get -y install libgl1-mesa-glx
RUN pip install -U langchain-cli pydantic==1.10.13
RUN pip install langchain==0.1.11
RUN pip install shortuuid
RUN pip install huggingface_hub
RUN mkdir -p /ws
ENV PYTHONPATH=/ws
COPY codegen-app /codegen-app
WORKDIR /codegen-app
CMD ["/bin/bash"]
