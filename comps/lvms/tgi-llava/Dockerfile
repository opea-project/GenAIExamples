# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

# Set environment variables
ENV LANG=en_US.UTF-8

ARG ARCH="cpu"

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    if [ ${ARCH} = "cpu" ]; then \
      pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /home/comps/lvms/tgi-llava/requirements.txt; \
    else \
      pip install --no-cache-dir -r /home/comps/lvms/tgi-llava/requirements.txt; \
    fi;

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/lvms/tgi-llava

ENTRYPOINT ["python", "lvm_tgi.py"]

