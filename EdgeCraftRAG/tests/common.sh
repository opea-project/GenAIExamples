#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    echo "[ $SERVICE_NAME ] Validating $SERVICE_NAME service..."
    local RESPONSE=$(curl -s -w "%{http_code}" -o ${LOG_PATH}/${SERVICE_NAME}.log -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    while [ ! -f ${LOG_PATH}/${SERVICE_NAME}.log ]; do
        sleep 1
    done
    local HTTP_STATUS="${RESPONSE: -3}"
    local CONTENT=$(cat ${LOG_PATH}/${SERVICE_NAME}.log)

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}_${DOCKER_NAME}.log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}_${DOCKER_NAME}.log
        exit 1
    fi
    sleep 1s
}

function check_gpu_usage() {
    echo $date > ${LOG_PATH}/gpu.log
    pci_address=$(lspci | grep -i '56a0' | awk '{print $1}')
    gpu_stats=$(sudo xpu-smi stats -d 0000:"$pci_address") #TODO need sudo
    gpu_utilization=$(echo "$gpu_stats" | grep -i "GPU Utilization" | awk -F'|' '{print $3}' | awk '{print $1}')
    memory_used=$(echo "$gpu_stats" | grep -i "GPU Memory Used" | awk -F'|' '{print $3}' | awk '{print $1}')
    memory_util=$(echo "$gpu_stats" | grep -i "GPU Memory Util" | awk -F'|' '{print $3}' | awk '{print $1}')

    echo "GPU Utilization (%): $gpu_utilization" >> ${LOG_PATH}/gpu.log
    echo "GPU Memory Used (MiB): $memory_used" >> ${LOG_PATH}/gpu.log
    echo "GPU Memory Util (%): $memory_util" >> ${LOG_PATH}/gpu.log

    if [ "$memory_used" -lt 1024 ]; then
        echo "GPU Memory Used is less than 1G. Please check."
        exit 1
    fi
}
