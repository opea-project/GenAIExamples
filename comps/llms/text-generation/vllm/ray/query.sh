# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

your_ip="0.0.0.0"

##query vllm ray service
curl http://${your_ip}:8006/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-2-7b-chat-hf", "messages": [{"role": "user", "content": "How are you?"}]}'

##query microservice
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_tokens":17,"top_p":1,"temperature":0.7,"frequency_penalty":0,"presence_penalty":0, "streaming":false}' \
  -H 'Content-Type: application/json'
