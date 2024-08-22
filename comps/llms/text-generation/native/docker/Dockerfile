

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# HABANA environment
# FROM vault.habana.ai/gaudi-docker/1.16.1/ubuntu22.04/habanalabs/pytorch-installer-2.2.2:latest as hpu
FROM opea/habanalabs:1.16.1-pytorch-installer-2.2.2 as hpu

ENV LANG=en_US.UTF-8
ARG REPO=https://github.com/huggingface/optimum-habana.git
ARG REPO_VER=v1.12.1

RUN apt-get update && \
    apt-get install git-lfs && \
    git-lfs install && \
    apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN pip install --upgrade-strategy eager optimum[habana] && \
    pip install git+https://github.com/HabanaAI/DeepSpeed.git@1.17.0

RUN git clone ${REPO} /home/user/optimum-habana && \
    cd /home/user/optimum-habana && git checkout ${REPO_VER} && \
    cd examples/text-generation && pip install -r requirements.txt && \
    cd /home/user/comps/llms/text-generation/native && pip install -r requirements.txt && \
    pip install --upgrade --force-reinstall pydantic

ENV PYTHONPATH=/root:/home/user

WORKDIR /home/user/comps/llms/text-generation/native

ENTRYPOINT ["python", "llm.py"]
