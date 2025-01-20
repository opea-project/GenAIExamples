#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

deployment_type="k8s"
node_number=1
service_port=8888
query_per_node=640

benchmark_tool_path="$(pwd)/GenAIEval"

usage() {
    echo "Usage: $0 [-d deployment_type] [-n node_number] [-i service_ip] [-p service_port]"
    echo "  -d deployment_type    ChatQnA deployment type, select between k8s and docker (default: k8s)"
    echo "  -n node_number        Test node number, required only for k8s deployment_type, (default: 1)"
    echo "  -i service_ip         chatqna service ip, required only for docker deployment_type"
    echo "  -p service_port       chatqna service port, required only for docker deployment_type, (default: 8888)"
    exit 1
}

while getopts ":d:n:i:p:" opt; do
    case ${opt} in
        d )
            deployment_type=$OPTARG
            ;;
        n )
            node_number=$OPTARG
            ;;
        i )
            service_ip=$OPTARG
            ;;
        p )
            service_port=$OPTARG
            ;;
        \? )
            echo "Invalid option: -$OPTARG" 1>&2
            usage
            ;;
        : )
            echo "Invalid option: -$OPTARG requires an argument" 1>&2
            usage
            ;;
    esac
done

if [[ "$deployment_type" == "docker" && -z "$service_ip" ]]; then
    echo "Error: service_ip is required for docker deployment_type" 1>&2
    usage
fi

if [[ "$deployment_type" == "k8s" && ( -n "$service_ip" || -n "$service_port" ) ]]; then
    echo "Warning: service_ip and service_port are ignored for k8s deployment_type" 1>&2
fi

function main() {
    if [[ ! -d ${benchmark_tool_path} ]]; then
        echo "Benchmark tool not found, setting up..."
        setup_env
    fi
    run_benchmark
}

function setup_env() {
    git clone https://github.com/opea-project/GenAIEval.git
    pushd ${benchmark_tool_path}
    python3 -m venv stress_venv
    source stress_venv/bin/activate
    pip install -r requirements.txt
    popd
}

function run_benchmark() {
    source ${benchmark_tool_path}/stress_venv/bin/activate
    export DEPLOYMENT_TYPE=${deployment_type}
    export SERVICE_IP=${service_ip:-"None"}
    export SERVICE_PORT=${service_port:-"None"}
    export LOAD_SHAPE=${load_shape:-"constant"}
    export CONCURRENT_LEVEL=${concurrent_level:-5}
    export ARRIVAL_RATE=${arrival_rate:-1.0}
    if [[ -z $USER_QUERIES ]]; then
        user_query=$((query_per_node*node_number))
        export USER_QUERIES="[${user_query}, ${user_query}, ${user_query}, ${user_query}]"
        echo "USER_QUERIES not configured, setting to: ${USER_QUERIES}."
    fi
    export WARMUP=$(echo $USER_QUERIES | sed -e 's/[][]//g' -e 's/,.*//')
    if [[ -z $WARMUP ]]; then export WARMUP=0; fi
    if [[ -z $TEST_OUTPUT_DIR ]]; then
        if [[ $DEPLOYMENT_TYPE == "k8s" ]]; then
            export TEST_OUTPUT_DIR="${benchmark_tool_path}/evals/benchmark/benchmark_output/node_${node_number}"
        else
            export TEST_OUTPUT_DIR="${benchmark_tool_path}/evals/benchmark/benchmark_output/docker"
        fi
        echo "TEST_OUTPUT_DIR not configured, setting to: ${TEST_OUTPUT_DIR}."
    fi

    envsubst < ./benchmark.yaml > ${benchmark_tool_path}/evals/benchmark/benchmark.yaml
    cd ${benchmark_tool_path}/evals/benchmark
    python benchmark.py
}

main
