#!/bin/bash
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -xe

cd ../.. # go to ChatQnA

# docker setup
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
bash serving/tgi_gaudi/launch_tgi_service.sh 1 8888

# launch redis
cd langchain/docker
docker compose -f docker-compose-langchain.yml up -d
cd ../../

docker exec -it qna-rag-redis-server \
    bash -c "cd /ws && python ingest.py"

# launch server
docker exec -it qna-rag-redis-server \
    bash -c "python app/server.py"

# request

# docker stop

# check response
