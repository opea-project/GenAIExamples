# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM $IMAGE_REPO/comps-base:$BASE_TAG
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    git
RUN git clone https://github.com/opea-project/GenAIExamples
COPY ./searchqna.py $HOME/searchqna.py

ENTRYPOINT ["python", "searchqna.py"]
