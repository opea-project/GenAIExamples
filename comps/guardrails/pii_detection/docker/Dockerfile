
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG C.UTF-8

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev \
    vim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/user/comps/guardrails/pii_detection/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

USER root

RUN mkdir -p /home/user/comps/guardrails/pii_detection/uploaded_files && chown -R user /home/user/comps/guardrails/pii_detection/uploaded_files
RUN mkdir -p /home/user/comps/guardrails/pii_detection/status && chown -R user /home/user/comps/guardrails/pii_detection/status

USER user

WORKDIR /home/user/comps/guardrails/pii_detection

ENTRYPOINT ["python", "pii_detection.py"]

