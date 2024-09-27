# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG UBUNTU_VER=22.04
FROM ubuntu:${UBUNTU_VER} as devel

ENV LANG=C.UTF-8

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    aspell \
    aspell-en \
    build-essential \
    git \
    python3 \
    python3-dev \
    python3-distutils \
    python3-pip \
    wget

USER user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/llms/utils/lm-eval/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/llms/utils/lm-eval


ENTRYPOINT ["python3", "self_hosted_hf.py"]
