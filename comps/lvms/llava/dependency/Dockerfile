# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim
RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/
USER user
# Set environment variables
ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/home/user:/usr/lib/habanalabs/:/optimum-habana

COPY comps /home/user/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/user/comps/lvms/llava/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

WORKDIR /home/user/comps/lvms/llava/dependency

ENTRYPOINT ["python", "llava_server.py", "--device", "cpu"]
