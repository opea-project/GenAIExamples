# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

QUERYFILE=$WORKDIR/datasets/crag_qas/crag_20_answerable_queries.csv
OUTFILE=$WORKDIR/datasets/crag_results/validation_5outof20.jsonl
PORT=9095

python src/test_agent_service.py --query_file $QUERYFILE --output_file $OUTFILE --port $PORT #--quick_test
