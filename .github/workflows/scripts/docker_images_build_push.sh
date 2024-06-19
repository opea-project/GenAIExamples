#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKSPACE=$PWD
IMAGE_REPO=${IMAGE_REPO:-$OPEA_IMAGE_REPO}
IMAGE_TAG=${IMAGE_TAG:-latest}

function docker_build() {
    # docker_build <IMAGE_NAME>
    IMAGE_NAME=$1
    micro_service=$2
    dockerfile_path=${WORKSPACE}/comps/${micro_service}
    if [ -f "$dockerfile_path/Dockerfile" ]; then
        DOCKERFILE_PATH="$dockerfile_path/Dockerfile"
    elif [ -f "$dockerfile_path/docker/Dockerfile" ]; then
        DOCKERFILE_PATH="$dockerfile_path/docker/Dockerfile"
    else
        echo "Dockerfile not found"
        exit 1
    fi
    echo "Building ${IMAGE_REPO}${IMAGE_NAME}:$IMAGE_TAG using Dockerfile $DOCKERFILE_PATH"

    docker build --no-cache -t ${IMAGE_REPO}${IMAGE_NAME}:$IMAGE_TAG -f $DOCKERFILE_PATH .
    docker push ${IMAGE_REPO}${IMAGE_NAME}:$IMAGE_TAG
    docker rmi ${IMAGE_REPO}${IMAGE_NAME}:$IMAGE_TAG
}

micro_service=$1
case ${micro_service} in
    "asr"|"tts")
        IMAGE_NAME="opea/${micro_service}"
        ;;
    "embeddings/langchain")
        IMAGE_NAME="opea/embedding-tei"
        ;;
    "retrievers/langchain")
        IMAGE_NAME="opea/retriever-redis"
        ;;
    "reranks/langchain")
        IMAGE_NAME="opea/reranking-tei"
        ;;
    "llms/text-generation/tgi")
        IMAGE_NAME="opea/llm-tgi"
        ;;
    "dataprep/redis/langchain")
        IMAGE_NAME="opea/dataprep-redis"
        ;;
    "llms/summarization/tgi")
        IMAGE_NAME="opea/llm-docsum-tgi"
        ;;
    *)
        echo "Not supported yet"
        exit 0
        ;;
esac
docker_build "${IMAGE_NAME}" "${micro_service}"
