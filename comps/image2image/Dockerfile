# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

# Set environment variables
ENV LANG=en_US.UTF-8

ARG ARCH="cpu"

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip && \
    if [ ${ARCH} = "cpu" ]; then pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /home/comps/image2image/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/image2image

RUN echo python image2image.py --bf16 >> run.sh

CMD bash run.sh
