# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM opea/comps-base:$BASE_TAG

COPY ./research_agents $HOME/research_agents
COPY ./requirements.txt $HOME/requirements.txt
COPY ./agent_factory.py $HOME/agent_factory.py
COPY ./research_agent.py $HOME/research_agent.py

USER root
ARG uvpip='uv pip install --system --no-cache-dir'
RUN pip install --no-cache-dir --upgrade pip setuptools uv && \
    $uvpip -r requirements.txt

USER user

ENTRYPOINT ["python", "research_agent.py"]