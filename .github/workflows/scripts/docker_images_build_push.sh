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
    if [[ "$IMAGE_NAME" == *"gaudi" ]]; then
        dockerfile_name="Dockerfile_hpu"
    else
        dockerfile_name="Dockerfile"
    fi
    if [ -f "$dockerfile_path/$dockerfile_name" ]; then
        DOCKERFILE_PATH="$dockerfile_path/$dockerfile_name"
    elif [ -f "$dockerfile_path/docker/$dockerfile_name" ]; then
        DOCKERFILE_PATH="$dockerfile_path/docker/$dockerfile_name"
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
hardware=$(echo $2 | cut -d- -f3)
case ${micro_service} in
    "asr"|"tts")
        IMAGE_NAME="opea/${micro_service}"
        ;;
    "embeddings/langchain")
        IMAGE_NAME="opea/embedding-tei"
        ;;
    "retrievers/langchain/redis")
        IMAGE_NAME="opea/retriever-redis"
        ;;
    "reranks/tei")
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
    "llms/faq-generation/tgi")
        IMAGE_NAME="opea/llm-faqgen-tgi"
        ;;
    "web_retrievers/langchain/chroma")
        IMAGE_NAME="opea/web-retriever-chroma"
        ;;
    "tts/speecht5")
        if [ "${hardware}" == "gaudi" ]; then IMAGE_NAME="opea/speecht5-gaudi"; else IMAGE_NAME="opea/speecht5"; fi
        ;;
    "asr/whisper")
        if [ "${hardware}" == "gaudi" ]; then IMAGE_NAME="opea/whisper-gaudi"; else IMAGE_NAME="opea/whisper"; fi
        ;;
    *)
        echo "Not supported yet"
        exit 0
        ;;
esac
docker_build "${IMAGE_NAME}" "${micro_service}"
