
# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identitier: Apache-2.0

FROM python:3.11-slim

COPY comps /home/comps

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /home/comps/guardrails/prompt_injection/predictionguard/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home

WORKDIR /home/comps/guardrails/prompt_injection/predictionguard

ENTRYPOINT ["python", "injection_predictionguard.py" ]
