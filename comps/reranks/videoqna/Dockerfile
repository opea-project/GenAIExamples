
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/user/comps/reranks/videoqna/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/reranks/videoqna

ENTRYPOINT ["python", "local_reranking.py"]
