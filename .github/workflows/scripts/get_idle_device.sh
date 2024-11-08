#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# How To Use
# device_index=$(bash .github/workflows/scripts/get_idle_device.sh)
# if [[ "$device_index" =~ ^[0-9]+$ ]]; then
#     export HABANA_VISIBLE_DEVICES=$device_index
# else
#     exit 1
# fi

declare -A dict
: "${USE_MODULE_ID:=0}"

function get_hpu_usage {
    local data=$(hl-smi -Q index,module_id,utilization.aip,memory.used -f csv)
    echo "$data"
}

function get_idle_device_id {
    local device_usage=$(get_hpu_usage)
    local available_indices=($(echo "$device_usage" | awk -F ', ' '$3=="0 %" && $4=="768 MiB" {print $1}'))
    local available_modules=($(echo "$device_usage" | awk -F ', ' '$3=="0 %" && $4=="768 MiB" {print $2}'))

    if [ ${#available_indices[@]} -gt 0 ]; then
        if [ $USE_MODULE_ID -eq 1 ]; then
            local random_id=${available_modules[$RANDOM % ${#available_modules[@]}]}
        else
            local random_id=${available_indices[$RANDOM % ${#available_indices[@]}]}
        fi
        echo "$random_id"
    else
        echo "-1"
    fi
}

function main {
    local timeout=$((2 * 60 * 60))
    local start_time=$(date +%s)
    while true; do
        local current_time=$(date +%s)
        local elapsed_time=$((current_time - start_time))
        if [ $elapsed_time -ge $timeout ]; then
            echo "Timeout reached."
            break
        fi

        local device_id=$(get_idle_device_id)
        if [[ "$device_id" =~ ^[0-9]+$ ]]; then
            echo "$device_id"
            break
        fi
        sleep 30s
    done
}

main
