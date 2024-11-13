# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use a base image
FROM python:3.11-slim

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/
USER user

ENV LANG=C.UTF-8
ARG ARCH=cpu

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /home/user/comps/animation/wav2lip/requirements.txt ;

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/animation/wav2lip

ENTRYPOINT ["python3", "animation.py"]
