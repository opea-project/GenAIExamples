# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

ARG BASE_TAG=latest
FROM opea/comps-base:$BASE_TAG

COPY ./hybridrag.py $HOME/hybridrag.py

ENTRYPOINT ["python", "hybridrag.py"]

