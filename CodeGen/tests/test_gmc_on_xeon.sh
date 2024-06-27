#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}

function init_codegen() {
    wget https://raw.githubusercontent.com/opea-project/GenAIInfra/main/microservices-connector/config/crd/bases/gmc.opea.io_gmconnectors.yaml
    wget https://raw.githubusercontent.com/opea-project/GenAIInfra/main/microservices-connector/config/rbac/gmc-manager-rbac.yaml
    wget https://raw.githubusercontent.com/opea-project/GenAIInfra/main/microservices-connector/config/manager/gmc-manager.yaml
    wget -O manifests/gmc-router.yaml https://raw.githubusercontent.com/opea-project/GenAIInfra/main/microservices-connector/config/gmcrouter/gmc-router.yaml

    # replace namespace for gmc-router and gmc-manager
    sed -i "s|namespace: system|namespace: $SYSTEM_NAMESPACE|g"  ./gmc-manager.yaml
    sed -i "s|namespace: system|namespace: $SYSTEM_NAMESPACE|g"  ./gmc-manager-rbac.yaml
    sed -i "s|name: system|name: $SYSTEM_NAMESPACE|g" ./gmc-manager-rbac.yaml
    # replace the mount dir "path: /mnt/model" with "path: $CHART_MOUNT"
    find . -name '*.yaml' -type f -exec sed -i "s#path: /mnt/models#path: $MOUNT_DIR#g" {} \;
    # replace the repository "image: opea/*" with "image: ${IMAGE_REPO}opea/"
    find . -name '*.yaml' -type f -exec sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" {} \;
    find . -name '*.yaml' -type f -exec sed -i "s#image: \"opea/*#image: ${IMAGE_REPO}opea\"/#g" {} \;
    # set huggingface token
    # find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
    find . -name '*.yaml' -type f -exec sed -i "s#insert-your-huggingface-token-here#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
    # replace namespace "default" with real namespace
    find . -name '*.yaml' -type f -exec sed -i "s#default.svc#$APP_NAMESPACE.svc#g" {} \;
}

function install_codegen() {
    # Make sure you have to use image tag $VERSION for microservice-connector installation
    echo "install microservice-connector, using repo $DOCKER_REGISTRY and tag $VERSION"
    echo "using namespace $SYSTEM_NAMESPACE and $APP_NAMESPACE"

    kubectl apply -f ./gmc.opea.io_gmconnectors.yaml
    kubectl apply -f ./gmc-manager-rbac.yaml
    kubectl create configmap gmcyaml -n $SYSTEM_NAMESPACE --from-file $(pwd)/../kubernetes/manifests
    kubectl apply -f ./gmc-manager.yaml

    # Wait until the gmc controller pod is ready
    wait_until_pod_ready "gmc-controller" $SYSTEM_NAMESPACE "gmc-controller"
    kubectl get pods -n $SYSTEM_NAMESPACE
    rm -f ./gmc.opea.io_gmconnectors.yaml ./gmc-manager-rbac.yaml ./gmc-manager.yaml manifests/gmc-router.yaml
}

function validate_codegen() {
    kubectl create ns $APP_NAMESPACE
    sed -i "s|namespace: codegen|namespace: $APP_NAMESPACE|g"  ./codegen_xeon.yaml
    kubectl apply -f ./codegen_xeon.yaml

    sleep 60

    ip_address=$(kubectl get svc $SERVICE_NAME -n $APP_NAMESPACE -o jsonpath='{.spec.clusterIP}')
    port=$(kubectl get svc $SERVICE_NAME -n $APP_NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    echo "try to curl http://${ip_address}:${port}/v1/codegen..."

    # generate a random logfile name to avoid conflict among multiple runners
    LOGFILE=$LOG_PATH/curlmega_$APP_NAMESPACE.log

    curl http://${ip_address}:${port}/v1/codegen -H "Content-Type: application/json" \
    -d '{"messages": "def print_hello_world():"}' > $LOGFILE
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Megaservice codegen failed, please check the logs in $LOGFILE!"
        exit 1
    fi

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOGFILE ]] && \
    [[ $(grep -c "print" $LOGFILE) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
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
    init_CodeGen)
        pushd ChatQnA/kubernetes
        init_codegen
        popd
        ;;
    install_CodeGen)
        pushd ChatQnA/kubernetes
        install_codegen
        popd
        ;;
    validate_CodeGen)
        pushd CodeGen/kubernetes
        SERVICE_NAME=codegen
        validate_codegen
        popd
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
