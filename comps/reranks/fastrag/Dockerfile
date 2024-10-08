# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.10-slim

ENV LANG=C.UTF-8

ARG ARCH="cpu"

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
    if [ ${ARCH} = "cpu" ]; then \
      pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /home/user/comps/reranks/fastrag/requirements.txt; \
      pip install --no-cache-dir .; \
      pip install --no-cache-dir .[intel]; \
    else \
      pip install --no-cache-dir -r /home/user/comps/reranks/fastrag/requirements.txt; \
      pip install --no-cache-dir .; \
      pip install --no-cache-dir .[intel]; \
    fi

ENV PYTHONPATH=$PYTHONPH:/home/user

WORKDIR /home/user/comps/reranks/fastrag

ENTRYPOINT ["python", "local_reranking.py"]
