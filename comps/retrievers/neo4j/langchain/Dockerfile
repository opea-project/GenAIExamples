# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

ENV no_proxy=localhost,127.0.0.1

ENV HUGGINGFACEHUB_API_TOKEN=dummy

ARG ARCH="cpu"

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /home/user/comps/retrievers/neo4j/langchain/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/retrievers/neo4j/langchain

ENTRYPOINT ["python", "retriever_neo4j.py"]
