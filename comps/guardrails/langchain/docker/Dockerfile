
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM langchain/langchain:latest

ENV LANG C.UTF-8

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
    pip install --no-cache-dir -r /home/user/comps/guardrails/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/guardrails/langchain

ENTRYPOINT ["python", "guardrails_tgi_gaudi.py"]

