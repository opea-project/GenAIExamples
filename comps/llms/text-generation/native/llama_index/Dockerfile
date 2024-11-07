# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# HABANA environment
FROM vault.habana.ai/gaudi-docker/1.18.0/ubuntu22.04/habanalabs/pytorch-installer-2.4.0 AS hpu

ENV LANG=en_US.UTF-8
ARG REPO=https://github.com/huggingface/optimum-habana.git
ARG REPO_VER=v1.12.1

RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    git-lfs \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

RUN git lfs install

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade-strategy eager optimum[habana] && \
    pip install --no-cache-dir git+https://github.com/HabanaAI/DeepSpeed.git@1.17.0

RUN git clone ${REPO} /home/user/optimum-habana && \
    cd /home/user/optimum-habana && git checkout ${REPO_VER} && \
    cd examples/text-generation && pip install --no-cache-dir -r requirements.txt && \
    cd /home/user/comps/llms/text-generation/native/llama_index && pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --upgrade --force-reinstall pydantic

ENV PYTHONPATH=/root:/home/user

WORKDIR /home/user/comps/llms/text-generation/native/llama_index

ENTRYPOINT ["python", "llm.py"]
