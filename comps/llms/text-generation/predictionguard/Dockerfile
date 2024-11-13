# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/comps/llms/text-generation/predictionguard/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/llms/text-generation/predictionguard

ENTRYPOINT ["bash", "entrypoint.sh"]
