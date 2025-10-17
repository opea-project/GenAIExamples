# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM opea/comps-base:$BASE_TAG

COPY ./deep_researcher.yaml $HOME/deep_researcher.yaml
COPY ./utils.py $HOME/utils.py
COPY ./requirements.txt $HOME/requirements.txt
COPY ./research_agent.py $HOME/research_agent.py

USER root
ARG uvpip='uv pip install --system --no-cache-dir'
RUN pip install --no-cache-dir --upgrade pip setuptools uv && \
    $uvpip -r requirements.txt

USER user

ENTRYPOINT ["python", "research_agent.py"]