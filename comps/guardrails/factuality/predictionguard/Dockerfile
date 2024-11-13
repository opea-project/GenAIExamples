# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identitier: Apache-2.0

FROM python:3.11-slim

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/comps/guardrails/factuality/predictionguard/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/guardrails/factuality/predictionguard

ENTRYPOINT ["python", "factuality_predictionguard.py" ]
