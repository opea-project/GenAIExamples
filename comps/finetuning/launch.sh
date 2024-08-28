# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

if [[ -n "$RAY_PORT" ]];then
    ray start --head --port $RAY_PORT
else
    ray start --head
    export RAY_PORT=8265
fi

export RAY_ADDRESS=http://127.0.0.1:$RAY_PORT
python finetuning_service.py
