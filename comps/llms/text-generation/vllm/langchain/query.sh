# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

your_ip="0.0.0.0"
model=$(curl http://localhost:8008/v1/models -s|jq -r '.data[].id')

curl http://${your_ip}:8008/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": "'$model'",
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'

##query microservice
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_tokens":17,"top_p":1,"temperature":0.7,"frequency_penalty":0,"presence_penalty":0, "streaming":false}' \
  -H 'Content-Type: application/json'
