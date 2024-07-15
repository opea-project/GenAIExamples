# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

your_ip="0.0.0.0"

curl http://${your_ip}:8008/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": "meta-llama/Meta-Llama-3-8B-Instruct",
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'

##query microservice
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_p":0.95,"temperature":0.01,"streaming":false}' \
  -H 'Content-Type: application/json'
