# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_NAME=python
ARG IMAGE_TAG=3.11-slim
FROM ${IMAGE_NAME}:${IMAGE_TAG} as base

ENV LANG C.UTF-8

RUN apt-get update -y && apt-get install -y \
    libgl1-mesa-glx \
    libjemalloc-dev && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

WORKDIR /home/user/GenAIComps

FROM base AS devel

ARG GenAICompsRepo="https://github.com/opea-project/GenAIComps"
ARG GenAICompsBranch="main"  # Branch name or Commit ID

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    curl

RUN curl -sSL --retry 5 ${GenAICompsRepo}/tarball/${GenAICompsBranch} | tar --strip-components=1 -xzf -

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/user/GenAIComps/requirements.txt && \
    pip install --no-cache-dir langchain_core

FROM base AS prod

ARG PYTHON=python3.11

COPY ./chatqna.py /home/user/chatqna.py

ENV PYTHONPATH=$PYTHONPATH:/home/user/GenAIComps

COPY --from=devel /usr/local/lib/${PYTHON}/site-packages /usr/local/lib/${PYTHON}/site-packages
COPY --from=devel /usr/local/bin /usr/local/bin
COPY --from=devel /home/user/GenAIComps /home/user/GenAIComps

USER user

WORKDIR /home/user

RUN echo 'ulimit -S -n 999999' >> ~/.bashrc

ENTRYPOINT ["python", "chatqna.py"]
