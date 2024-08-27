# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG UBUNTU_VER=22.04
FROM ubuntu:${UBUNTU_VER} as devel

ENV LANG=C.UTF-8

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    aspell \
    aspell-en \
    build-essential \
    git \
    python3 \
    python3-dev \
    python3-distutils \
    python3-pip \
    wget

USER user

ARG REPO_COMPS=https://github.com/opea-project/GenAIComps.git
ARG BRANCH=main
RUN git clone --single-branch --branch=${BRANCH} ${REPO_COMPS} /home/user/GenAIComps/ && \
    cd /home/user/GenAIComps/ && python3 setup.py install && \
    pip install --no-cache-dir -r /home/user/GenAIComps/comps/llms/utils/lm-eval/requirements.txt

WORKDIR /home/user/GenAIComps/comps/llms/utils/lm-eval/

ENTRYPOINT ["python3", "self_hosted_hf.py"]
