# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

# Set environment variables
ENV LANG=en_US.UTF-8

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/comps/lvms/video-llama/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/lvms/video-llama

ENTRYPOINT ["python", "lvm.py"]
