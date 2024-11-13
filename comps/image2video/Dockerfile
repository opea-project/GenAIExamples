# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

# Set environment variables
ENV LANG=en_US.UTF-8

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/comps/image2video/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/image2video

ENTRYPOINT ["python", "image2video.py"]
