# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

ARG ARCH="cpu"
ARG SERVICE="all"

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    git \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN if [ ${ARCH} = "cpu" ]; then \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu; \
fi && \
if [ ${SERVICE} = "videoqna" ]; then \
    pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/user/comps/rerankings/src/requirements_videoqna.txt; \
elif [ ${SERVICE} = "all" ]; then \
    git clone https://github.com/IntelLabs/fastRAG.git /home/user/fastRAG && \
    cd /home/user/fastRAG && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir .[intel] && \
    pip install --no-cache-dir -r /home/user/comps/rerankings/src/requirements_videoqna.txt; \
fi && \
pip install --no-cache-dir --upgrade pip setuptools && \
pip install --no-cache-dir -r /home/user/comps/rerankings/src/requirements.txt;


ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/rerankings/src

ENTRYPOINT ["python", "opea_reranking_microservice.py"]
