# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

<<<<<<< HEAD
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export ip_address=$(hostname -I | awk '{print $1}')
export recursion_limit_worker=12
export recursion_limit_supervisor=10
=======
export ip_address=$(hostname -I | awk '{print $1}')
export recursion_limit=12
>>>>>>> main
export model="gpt-4o-mini-2024-07-18"
export temperature=0
export max_new_tokens=512
export OPENAI_API_KEY=${OPENAI_API_KEY}
export WORKER_AGENT_URL="http://${ip_address}:9095/v1/chat/completions"
<<<<<<< HEAD
export RETRIEVAL_TOOL_URL="http://${ip_address}:8889/v1/retrievaltool"
=======
>>>>>>> main
export CRAG_SERVER=http://${ip_address}:8080

docker compose -f docker-compose-agent-openai.yaml up -d
