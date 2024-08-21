#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}

function install_searchqa() {
    kubectl create ns $APP_NAMESPACE
    sed -i "s|namespace: searchqa|namespace: $APP_NAMESPACE|g"  ./searchQnA_xeon.yaml
    sed -i "s|insert-your-google-api-key-here|$GOOGLE_API_KEY|g"  ./searchQnA_xeon.yaml
    sed -i "s|insert-your-google-cse-id-here|$GOOGLE_CSE_ID|g"  ./searchQnA_xeon.yaml
    kubectl apply -f ./searchQnA_xeon.yaml

    # Wait until the router service is ready
    echo "Waiting for the searchqa router service to be ready..."
    wait_until_pod_ready "searchqa router" $APP_NAMESPACE "router-service"
    output=$(kubectl get pods -n $APP_NAMESPACE)
    echo $output
}

function validate_searchqa() {
    # deploy client pod for testing
    kubectl create deployment client-test -n $APP_NAMESPACE --image=python:3.8.13 -- sleep infinity

    # wait for client pod ready
    wait_until_pod_ready "client-test" $APP_NAMESPACE "client-test"
    # giving time to populating data
    sleep 60

    kubectl get pods -n $APP_NAMESPACE
    # send request to searchqa
    export CLIENT_POD=$(kubectl get pod -n $APP_NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
    echo "$CLIENT_POD"
    accessUrl=$(kubectl get gmc -n $APP_NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='searchqa')].status.accessUrl}")
    kubectl exec "$CLIENT_POD" -n $APP_NAMESPACE -- curl $accessUrl  -X POST  -d '{"text":"How many gold medals does USA win in olympics 2024? Give me also the source link."}' -H 'Content-Type: application/json' > $LOG_PATH/gmc_searchqa.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "searchqna failed, please check the logs in ${LOG_PATH}!"
        exit 1
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOG_PATH/gmc_searchqa.log ]] && \
    [[ $(grep -c "[DONE]" $LOG_PATH/gmc_searchqa.log) != 0 ]]; then
        status=true
    fi
    if [ $status == false ]; then
        if [[ -f $LOG_PATH/gmc_searchqa.log ]]; then
            cat $LOG_PATH/gmc_searchqa.log
        fi
        echo "Response check failed, please check the logs in artifacts!"
        cat $LOG_PATH/gmc_searchqa.log
        exit 1
    else
        echo "Response check succeed!"
    fi
}

function wait_until_pod_ready() {
    echo "Waiting for the $1 to be ready..."
    max_retries=30
    retry_count=0
    while ! is_pod_ready $2 $3; do
        if [ $retry_count -ge $max_retries ]; then
            echo "$1 is not ready after waiting for a significant amount of time"
            get_gmc_controller_logs
            exit 1
        fi
        echo "$1 is not ready yet. Retrying in 10 seconds..."
        sleep 10
        output=$(kubectl get pods -n $2)
        echo $output
        retry_count=$((retry_count + 1))
    done
}

function is_pod_ready() {
    if [ "$2" == "gmc-controller" ]; then
      pod_status=$(kubectl get pods -n $1 -o jsonpath='{.items[].status.conditions[?(@.type=="Ready")].status}')
    else
      pod_status=$(kubectl get pods -n $1 -l app=$2 -o jsonpath='{.items[].status.conditions[?(@.type=="Ready")].status}')
    fi
    if [ "$pod_status" == "True" ]; then
        return 0
    else
        return 1
    fi
}

function get_gmc_controller_logs() {
    # Fetch the name of the pod with the app-name gmc-controller in the specified namespace
    pod_name=$(kubectl get pods -n $SYSTEM_NAMESPACE -l control-plane=gmc-controller -o jsonpath='{.items[0].metadata.name}')

    # Check if the pod name was found
    if [ -z "$pod_name" ]; then
        echo "No pod found with app-name gmc-controller in namespace $SYSTEM_NAMESPACE"
        return 1
    fi

    # Get the logs of the found pod
    echo "Fetching logs for pod $pod_name in namespace $SYSTEM_NAMESPACE..."
    kubectl logs $pod_name -n $SYSTEM_NAMESPACE
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

case "$1" in
    install_SearchQnA)
        pushd SearchQnA/kubernetes
        install_searchqa
        popd
        ;;
    validate_SearchQnA)
        pushd SearchQnA/kubernetes
        validate_searchqa
        popd
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
