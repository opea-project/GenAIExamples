# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

# Set environment variables
ENV LANG=en_US.UTF-8

ARG ARCH="cpu"

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    python3-pip \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

COPY comps /home/user/comps

USER user

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then \
      pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /home/user/comps/retrievers/redis/llama_index/requirements.txt; \
    else \
      pip install --no-cache-dir -r /home/user/comps/retrievers/redis/llama_index/requirements.txt; \
    fi;

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/retrievers/redis/llama_index

ENTRYPOINT ["python", "retriever_redis.py"]
