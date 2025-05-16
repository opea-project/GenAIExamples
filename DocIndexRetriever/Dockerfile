# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG BASE_TAG=latest
FROM opea/comps-base:$BASE_TAG

COPY ./retrieval_tool.py $HOME/retrieval_tool.py

ENTRYPOINT ["python", "retrieval_tool.py"]
