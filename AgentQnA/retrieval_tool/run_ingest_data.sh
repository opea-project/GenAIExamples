# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FILEDIR=${WORKDIR}/GenAIExamples/AgentQnA/example_data/
FILENAME=test_docs_music.jsonl

# AgentQnA ingestion script requires following packages
packages=("requests" "tqdm")

# Check if packages are installed
for package in "${packages[@]}"; do
  if pip freeze | grep -q "$package="; then
    echo "$package is installed"
  else
    echo "$package is not installed"
    pip install --no-cache-dir "$package"
  fi
done

python3 index_data.py --filedir ${FILEDIR} --filename ${FILENAME} --host_ip $host_ip
