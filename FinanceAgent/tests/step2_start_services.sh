#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
set -xe

export WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export IP_ADDRESS=$(hostname -I | awk '{print $1}')
export HOST_IP=${IP_ADDRESS}
LOG_PATH=$WORKPATH

function start_all_services() {
    case $1 in
        "gaudi_vllm")
            echo "==================== Start all services for Gaudi ===================="
            docker compose -f $WORKPATH/docker_compose/intel/hpu/gaudi/compose.yaml up -d

            until [[ "$n" -ge 200 ]] || [[ $ready == true ]]; do
                docker logs vllm-gaudi-server &> ${LOG_PATH}/vllm-gaudi-service.log
                n=$((n+1))
                if grep -q "Uvicorn running on" ${LOG_PATH}/vllm-gaudi-service.log; then
                    break
                fi
                if grep -q "No such container" ${LOG_PATH}/vllm-gaudi-service.log; then
                    echo "container vllm-gaudi-server not found"
                    exit 1
                fi
                sleep 10s
            done
            ;;
        "xeon")
            echo "==================== Start all services for Xeon ===================="
            docker compose -f $WORKPATH/docker_compose/intel/cpu/xeon/compose_openai.yaml up -d
            until [[ "$n" -ge 200 ]] || [[ $ready == true ]]; do
                docker logs docsum-vllm-xeon &> ${LOG_PATH}/docsum-vllm-xeon-service.log
                n=$((n+1))
                if grep -q "Uvicorn running on" ${LOG_PATH}/docsum-vllm-xeon-service.log; then
                    break
                fi
                if grep -q "No such container" ${LOG_PATH}/docsum-vllm-xeon-service.log; then
                    echo "container docsum-vllm-xeon not found"
                    exit 1
                fi
                sleep 10s
            done
            ;;
        *)
            echo "Invalid argument"
            exit 1
            ;;
    esac

    sleep 10s
    echo "Service started successfully"
}

function main() {
    start_all_services $1
}

main $1
