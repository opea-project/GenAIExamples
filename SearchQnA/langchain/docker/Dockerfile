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
RUN rm -rf /etc/ssh/ssh_host*

# Set environment variables
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/home/user:/usr/lib/habanalabs/

# Install required branch
RUN git clone https://github.com/Spycsh/langchain.git /langchain -b master && \
    pip install --no-cache-dir /langchain/libs/langchain && \
    pip install --no-cache-dir /langchain/libs/community && \
    rm -rf /langchain

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY requirements.txt /tmp/requirements.txt

# Install dependency
RUN pip install --no-cache-dir -U -r /tmp/requirements.txt

# work dir should contains the server
# make sure it can be edited by user
WORKDIR /home/user/qna-app
COPY qna-app /home/user/qna-app

ENTRYPOINT ["python", "server.py"]
