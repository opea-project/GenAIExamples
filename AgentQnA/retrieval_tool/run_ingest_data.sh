# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FILEDIR=${WORKDIR}/GenAIExamples/AgentQnA/example_data/
FILENAME=test_docs_music.jsonl

python3 index_data.py --filedir ${FILEDIR} --filename ${FILENAME} --host_ip $host_ip
