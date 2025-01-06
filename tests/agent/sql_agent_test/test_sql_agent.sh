#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#set -xe

# this script should be run from tests directory
#  bash agent/sql_agent_test/test_sql_agent.sh

WORKPATH=$(dirname "$PWD")
echo $WORKPATH
LOG_PATH="$WORKPATH/tests"

# WORKDIR is one level up from GenAIComps
export WORKDIR=$(dirname "$WORKPATH")
echo $WORKDIR

export agent_image="opea/agent:comps"
export agent_container_name="test-comps-agent-endpoint"

export ip_address=$(hostname -I | awk '{print $1}')

vllm_port=8086
vllm_volume=${HF_CACHE_DIR}

export model=meta-llama/Meta-Llama-3.1-70B-Instruct
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export LLM_ENDPOINT_URL="http://${ip_address}:${vllm_port}"
export temperature=0.01
export max_new_tokens=4096
export TOOLSET_PATH=$WORKPATH/comps/agent/src/tools/ # $WORKPATH/tests/agent/sql_agent_test/
echo "TOOLSET_PATH=${TOOLSET_PATH}"
export recursion_limit=15
export db_name=california_schools
export db_path="sqlite:////home/user/TAG-Bench/dev_folder/dev_databases/${db_name}/${db_name}.sqlite"

# for using Google search API
export GOOGLE_CSE_ID=${GOOGLE_CSE_ID}
export GOOGLE_API_KEY=${GOOGLE_API_KEY}


# download the test data
function prepare_data() {
    cd $WORKDIR

    echo "Downloading data..."
    git clone https://github.com/TAG-Research/TAG-Bench.git
    cd TAG-Bench/setup
    chmod +x get_dbs.sh
    ./get_dbs.sh

    echo "Split data..."
    cd $WORKPATH/tests/agent/sql_agent_test
    bash run_data_split.sh

    echo "Data preparation done!"
}

function remove_data() {
    echo "Removing data..."
    cd $WORKDIR
    rm -rf TAG-Bench
    echo "Data removed!"
}


function generate_hints_for_benchmark() {
    echo "Generating hints for benchmark..."
    cd $WORKPATH/tests/agent/sql_agent_test
    python3 generate_hints_file.py
}

function build_docker_images() {
    echo "Building the docker images"
    cd $WORKPATH
    echo $WORKPATH
    docker build --no-cache -t $agent_image --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -f comps/agent/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/agent built fail"
        exit 1
    else
        echo "opea/agent built successful"
    fi
}

function build_vllm_docker_images() {
    echo "Building the vllm docker images"
    cd $WORKPATH
    echo $WORKPATH
    if [ ! -d "./vllm" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git
    fi
    cd ./vllm-fork
    docker build --no-cache -f Dockerfile.hpu -t opea/vllm-gaudi:comps --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    if [ $? -ne 0 ]; then
        echo "opea/vllm-gaudi:comps failed"
        exit 1
    else
        echo "opea/vllm-gaudi:comps successful"
    fi
}

function start_vllm_service() {
    # redis endpoint
    echo "token is ${HF_TOKEN}"

    #single card
    echo "start vllm gaudi service"
    echo "**************model is $model**************"
    docker run -d --runtime=habana --rm --name "test-comps-vllm-gaudi-service" -e HABANA_VISIBLE_DEVICES=0,1,2,3 -p $vllm_port:80 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host opea/vllm-gaudi:comps --model ${model} --host 0.0.0.0 --port 80 --block-size 128 --max-seq-len-to-capture 16384 --tensor-parallel-size 4
    sleep 5s
    echo "Waiting vllm gaudi ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-vllm-gaudi-service &> ${LOG_PATH}/vllm-gaudi-service.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/vllm-gaudi-service.log; then
            break
        fi
        if grep -q "No such container" ${LOG_PATH}/vllm-gaudi-service.log; then
            echo "container test-comps-vllm-gaudi-service not found"
            exit 1
        fi
        sleep 5s
    done
    sleep 5s
    echo "Service started successfully"
}
# launch the agent
function start_sql_agent_llama_service() {
    echo "Starting sql_agent_llama agent microservice"
    docker compose -f $WORKPATH/tests/agent/sql_agent_llama.yaml up -d
    sleep 3m
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}


function start_sql_agent_openai_service() {
    export OPENAI_API_KEY=${OPENAI_API_KEY}
    echo "Starting sql_agent_openai agent microservice"
    docker compose -f $WORKPATH/tests/agent/sql_agent_openai.yaml up -d
    sleep 3m
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

# run the test
function run_test() {
    echo "Running test..."
    cd $WORKPATH/tests/agent/
    python3 test.py --test-sql-agent
}

function run_benchmark() {
    echo "Running benchmark..."
    cd $WORKPATH/tests/agent/sql_agent_test
    query_file=${WORKDIR}/TAG-Bench/query_by_db/query_california_schools.csv
    outdir=$WORKDIR/sql_agent_output
    outfile=california_school_agent_test_result.csv
    python3 test_tag_bench.py --query_file $query_file --output_dir $outdir --output_file $outfile
}


echo "Preparing data...."
prepare_data

echo "launching sql_agent_llama service...."
start_sql_agent_llama_service

# echo "launching sql_agent_openai service...."
# start_sql_agent_openai_service

echo "Running test...."
run_test

echo "Removing data...."
remove_data
