
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM langchain/langchain:latest

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/reranks/neural-speed/requirements.txt

RUN pip3 install llmspec mosec msgspec httpx requests
RUN pip3 install torch==2.2.2 --trusted-host download.pytorch.org --index-url https://download.pytorch.org/whl/cpu

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/reranks/neural-speed

ENTRYPOINT ["python", "reranking_neuralspeed_svc.py"]

