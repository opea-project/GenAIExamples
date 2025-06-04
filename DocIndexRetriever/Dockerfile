# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG IMAGE_REPO=opea
ARG BASE_TAG=latest
FROM $IMAGE_REPO/comps-base:$BASE_TAG

COPY ./retrieval_tool.py $HOME/retrieval_tool.py

ENTRYPOINT ["python", "retrieval_tool.py"]
