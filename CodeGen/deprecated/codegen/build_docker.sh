#!/bin/bash



# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

docker build . -t intel/gen-ai-examples:copilot --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
