#!/usr/bin/env bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

pip --no-cache-dir install -r requirements-runtime.txt

python opea_hallucination_detection_microservice.py
