# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM opea/comps-base:$BASE_TAG
FROM $IMAGE_REPO/comps-base:$BASE_TAG

COPY ./audioqna.py $HOME/audioqna.py

ENTRYPOINT ["python", "audioqna.py"]
