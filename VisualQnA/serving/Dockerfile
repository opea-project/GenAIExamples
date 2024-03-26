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

# HABANA environment
FROM vault.habana.ai/gaudi-docker/1.14.0/ubuntu22.04/habanalabs/pytorch-installer-2.1.1 AS hpu

# Set environment variables
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/home/user:/usr/lib/habanalabs/:/optimum-habana

# Install required branch
RUN git clone https://github.com/lkk12014402/optimum-habana.git /optimum-habana -b enable_llava_generation

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY requirements.txt /tmp/requirements.txt

# Install dependency
RUN pip install --no-cache-dir -U -r /tmp/requirements.txt

# work dir should contains the server
WORKDIR /llava_server
COPY llava_server /llava_server

ENTRYPOINT ["python", "llava_server.py"]
