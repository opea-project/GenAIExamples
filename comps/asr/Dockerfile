# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG=C.UTF-8

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/comps/asr/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/asr

ENTRYPOINT ["python", "asr.py"]