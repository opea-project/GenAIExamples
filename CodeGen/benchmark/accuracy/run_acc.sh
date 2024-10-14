

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

python main.py --model $1 \
  --tasks humaneval \
  --codegen_url $2 \
  --max_length_generation 2048 \
  --batch_size 1  \
  --save_generations \
  --save_references \
  --allow_code_execution
