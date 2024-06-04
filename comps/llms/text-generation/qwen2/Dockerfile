

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# HABANA environment
FROM vault.habana.ai/gaudi-docker/1.15.1/ubuntu22.04/habanalabs/pytorch-installer-2.2.0:latest as hpu

ENV LANG=en_US.UTF-8
ARG REPO=https://github.com/huggingface/optimum-habana.git
ARG REPO_VER=v1.11.1

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
COPY comps/llm/text-generation/qwen2/qwen2.patch /home/user/qwen2.patch

SHELL ["/bin/bash", "--login", "-c"]
RUN git clone --single-branch -b ${REPO_VER} ${REPO} /optimum-habana

ENV PYTHONPATH=/root:/home/user

RUN cd /optimum-habana && git apply /qwen2.patch && \
    cd /optimum-habana/examples/text-generation && pip install -r requirements.txt && \
    cd /optimum-habana && python setup.py install

WORKDIR /home/user/comps/llms/text-generation/qwen2

ENTRYPOINT ["python", "llm.py"]
