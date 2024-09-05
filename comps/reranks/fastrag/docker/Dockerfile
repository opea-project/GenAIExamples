# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.10-slim

ENV LANG=C.UTF-8

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    git \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN git clone https://github.com/IntelLabs/fastRAG.git /home/user/fastRAG && \
    cd /home/user/fastRAG && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/reranks/requirements.txt && \
    pip install --no-cache-dir -r /home/user/comps/reranks/fastrag/requirements.txt && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir .[intel]

ENV PYTHONPATH=$PYTHONPH:/home/user

WORKDIR /home/user/comps/reranks/fastrag

ENTRYPOINT ["python", "local_reranking.py"]
