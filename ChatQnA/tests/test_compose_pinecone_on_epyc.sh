#!/bin/bash
# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"./data"}

WORKPATH=$(dirname "$PWD")
mkdir -p "$WORKPATH/tests/logs"
LOG_PATH="$WORKPATH/tests/logs"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
	opea_branch=${opea_branch:-"main"}

	cd $WORKPATH/docker_image_build
	git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
	pushd GenAIComps
	echo "GenAIComps test commit is $(git rev-parse HEAD)"
	docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
	popd && sleep 1s
	git clone https://github.com/vllm-project/vllm.git && cd vllm
	VLLM_VER=v0.9.0.1
	echo "Check out vLLM tag ${VLLM_VER}"
	git checkout ${VLLM_VER} &>/dev/null
	VLLM_REQ_FILE="requirements/cpu.txt"
	if ! grep -q "^transformers" "$VLLM_REQ_FILE"; then
		echo "Adding transformers<4.54.0 to $VLLM_REQ_FILE"
		echo "transformers<4.54.0" >>"$VLLM_REQ_FILE"
	fi
	cd ../

	echo "Build all the images with --no-cache, check docker_image_build.log for details..."
	service_list="chatqna chatqna-ui dataprep retriever vllm nginx"
	docker compose -f build.yaml build ${service_list} --no-cache >${LOG_PATH}/docker_image_build.log

	docker images && sleep 1s
}

function start_services() {
	cd $WORKPATH/docker_compose/amd/cpu/epyc/
	export no_proxy=${no_proxy},${ip_address}
	export PINECONE_API_KEY=${PINECONE_KEY_LANGCHAIN_TEST}
	export PINECONE_INDEX_NAME="langchain-test"
	export INDEX_NAME="langchain-test"
	export LOGFLAG=true
	source set_env.sh

	# Start Docker Containers
	docker compose -f compose_pinecone.yaml up -d --quiet-pull >${LOG_PATH}/start_services_with_compose.log

	n=0
	until [[ "$n" -ge 100 ]]; do
		docker logs vllm-service >${LOG_PATH}/vllm_service_start.log 2>&1
		if grep -q complete ${LOG_PATH}/vllm_service_start.log; then
			break
		fi
		sleep 5s
		n=$((n + 1))
	done
}

function validate_service() {
	local URL="$1"
	local EXPECTED_RESULT="$2"
	local SERVICE_NAME="$3"
	local DOCKER_NAME="$4"
	local INPUT_DATA="$5"

	if [[ $SERVICE_NAME == *"dataprep_upload_file"* ]]; then
		cd $LOG_PATH
		HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
	elif [[ $SERVICE_NAME == *"dataprep_del"* ]]; then
		HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "all"}' -H 'Content-Type: application/json' "$URL")
	else
		HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
	fi
	HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
	RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

	docker logs ${DOCKER_NAME} >>${LOG_PATH}/${SERVICE_NAME}.log

	# check response status
	if [ "$HTTP_STATUS" -ne "200" ]; then
		echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
		exit 1
	else
		echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
	fi
	echo "Response"
	echo $RESPONSE_BODY
	echo "Expected Result"
	echo $EXPECTED_RESULT
	# check response body
	if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
		echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
		exit 1
	else
		echo "[ $SERVICE_NAME ] Content is as expected."
	fi

	sleep 1s
}

function validate_microservices() {
	# Check if the microservices are running correctly.

	# tei for embedding service
	validate_service \
		"${ip_address}:6006/embed" \
		"[[" \
		"tei-embedding" \
		"tei-embedding-server" \
		'{"inputs":"What is Deep Learning?"}'

	sleep 1m # retrieval can't curl as expected, try to wait for more time

	# test /v1/dataprep/delete
	validate_service \
		"http://${ip_address}:6007/v1/dataprep/delete" \
		'{"status":true}' \
		"dataprep_del" \
		"dataprep-pinecone-server"

	# test /v1/dataprep/ingest upload file
	echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." >$LOG_PATH/dataprep_file.txt
	validate_service \
		"http://${ip_address}:6007/v1/dataprep/ingest" \
		"Data preparation succeeded" \
		"dataprep_upload_file" \
		"dataprep-pinecone-server"

	# retrieval microservice
	test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
	validate_service \
		"${ip_address}:7000/v1/retrieval" \
		" " \
		"retrieval" \
		"retriever-pinecone-server" \
		"{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

	# tei for rerank microservice
	echo "Validating reranking service"
	validate_service \
		"${ip_address}:8808/rerank" \
		'{"index":1,"score":' \
		"tei-rerank" \
		"tei-reranking-server" \
		'{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

	# vllm for llm service
	echo "Validating llm service"
	validate_service \
		"${ip_address}:9009/v1/chat/completions" \
		"content" \
		"vllm-llm" \
		"vllm-service" \
		'{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}'
}

function validate_megaservice() {
	# Curl the Mega Service
	validate_service \
		"${ip_address}:8888/v1/chatqna" \
		"data: " \
		"chatqna-megaservice" \
		"chatqna-epyc-backend-server" \
		'{"messages": "What is the revenue of Nike in 2023?"}'

}

function validate_frontend() {
	echo "[ TEST INFO ]: --------- frontend test started ---------"
	cd $WORKPATH/ui/svelte
	local conda_env_name="OPEA_e2e"
	export PATH=${HOME}/miniforge3/bin/:$PATH
	if conda info --envs | grep -q "$conda_env_name"; then
		echo "$conda_env_name exist!"
	else
		conda create -n ${conda_env_name} python=3.12 -y
	fi
	CONDA_ROOT=$(conda info --base)
	source "${CONDA_ROOT}/etc/profile.d/conda.sh"
	conda activate ${conda_env_name}
	echo "[ TEST INFO ]: --------- conda env activated ---------"

	sed -i "s/localhost/$ip_address/g" playwright.config.ts

	conda install -c conda-forge nodejs=22.6.0 -y
	# npm install && npm ci && npx playwright install --with-deps
	npm install && npm ci && npx playwright install
	node -v && npm -v && pip list

	exit_status=0
	npx playwright test || exit_status=$?

	if [ $exit_status -ne 0 ]; then
		echo "[TEST INFO]: ---------frontend test failed---------"
		exit $exit_status
	else
		echo "[TEST INFO]: ---------frontend test passed---------"
	fi
}

function stop_docker() {
	echo "In stop docker"
	echo $WORKPATH
	cd $WORKPATH/docker_compose/amd/cpu/epyc/
	docker compose -f compose_pinecone.yaml down
}

function main() {

	echo "::group::stop_docker"
	stop_docker
	echo "::endgroup::"

	echo "::group::build_docker_images"
	if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
	echo "::endgroup::"

	echo "::group::start_services"
	start_services
	echo "::endgroup::"

	echo "::group::validate_microservices"
	validate_microservices
	echo "::endgroup::"

	echo "::group::validate_megaservice"
	validate_megaservice
	echo "::endgroup::"

	echo "::group::stop_docker"
	stop_docker
	echo "::endgroup::"

	docker system prune -f
}

main
