# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM langchain/langchain

ARG http_proxy
ARG https_proxy
ENV http_proxy=$http_proxy
ENV https_proxy=$https_proxy

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        libgl1-mesa-glx \
        libjemalloc-dev

RUN pip install --upgrade pip \
    sentence-transformers \
    langchain-cli \
    pydantic==1.10.13 \
    langchain==0.1.12 \
    poetry \
    langchain_benchmarks \
    pyarrow \
    jupyter \
    docx2txt \
    pypdf \
    beautifulsoup4 \
    python-multipart \
    intel-extension-for-pytorch \
    intel-openmp

ENV PYTHONPATH=/ws:/summarize-app/app

COPY summarize-app /summarize-app
WORKDIR /summarize-app

CMD ["/bin/bash"]
