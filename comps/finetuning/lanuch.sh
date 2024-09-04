# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

if [[ -n "$RAY_PORT" ]];then
    export RAY_ADDRESS=http://127.0.0.1:$RAY_PORT
    ray start --head --port $RAY_PORT
else
    export RAY_ADDRESS=http://127.0.0.1:8265
    ray start --head
fi

python finetuning_service.py
