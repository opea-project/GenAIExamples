#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}

function init_chatqna() {
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
    find . -name '*.yaml' -type f -exec sed -i "s#\${HUGGINGFACEHUB_API_TOKEN}#$(cat /home/$USER_ID/.cache/huggingface/token)#g" {} \;
    # replace namespace "default" with real namespace
    find . -name '*.yaml' -type f -exec sed -i "s#default.svc#$APP_NAMESPACE.svc#g" {} \;
}

function install_chatqna() {
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
}

function validate_chatqna() {
   kubectl create ns $APP_NAMESPACE
   sed -i "s|namespace: chatqa|namespace: $APP_NAMESPACE|g"  ./chatQnA_xeon.yaml
   kubectl apply -f ./chatQnA_xeon.yaml

   # Wait until the router service is ready
   echo "Waiting for the chatqa router service to be ready..."
   wait_until_pod_ready "chatqna router" $APP_NAMESPACE "router-service"
   output=$(kubectl get pods -n $APP_NAMESPACE)
   echo $output

   # Wait until the tgi pod is ready
   TGI_POD_NAME=$(kubectl get pods --namespace=$APP_NAMESPACE | grep ^tgi-service | awk '{print $1}')
   kubectl describe pod $TGI_POD_NAME -n $APP_NAMESPACE
   kubectl wait --for=condition=ready pod/$TGI_POD_NAME --namespace=$APP_NAMESPACE --timeout=300s


   # deploy client pod for testing
   kubectl create deployment client-test -n $APP_NAMESPACE --image=python:3.8.13 -- sleep infinity

   # wait for client pod ready
   wait_until_pod_ready "client-test" $APP_NAMESPACE "client-test"

   max_retry=20
   # make sure microservice retriever is ready
   # try to curl retriever-svc for max_retry times
   for ((i=1; i<=max_retry; i++))
   do
     curl http://retriever-svc.$APP_NAMESPACE:7000/v1/retrieval -X POST \
       -d '{"text":"What is the revenue of Nike in 2023?","embedding":"'"${your_embedding}"'"}' \
       -H 'Content-Type: application/json' && break
     sleep 10
   done

   # if i is bigger than max_retry, then exit with error
   if [ $i -gt $max_retry ]; then
       echo "Microservice failed, exit with error."
       exit 1
   fi

   kubectl get pods -n $APP_NAMESPACE
   # send request to chatqnA
   export CLIENT_POD=$(kubectl get pod -n $APP_NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
   echo "$CLIENT_POD"
   accessUrl=$(kubectl get gmc -n $APP_NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='chatqa')].status.accessUrl}")
   kubectl exec "$CLIENT_POD" -n $APP_NAMESPACE -- curl $accessUrl  -X POST  -d '{"text":"What is the revenue of Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json' > $LOG_PATH/curl_chatqna.log
   exit_code=$?
   if [ $exit_code -ne 0 ]; then
       echo "chatqna failed, please check the logs in ${LOG_PATH}!"
       exit 1
   fi

   echo "Checking response results, make sure the output is reasonable. "
   local status=false
   if [[ -f $LOG_PATH/curl_chatqna.log ]] && \
   [[ $(grep -c "billion" $LOG_PATH/curl_chatqna.log) != 0 ]]; then
       status=true
   fi
   if [ $status == false ]; then
       if [[ -f $LOG_PATH/curl_chatqna.log ]]; then
           cat $LOG_PATH/curl_chatqna.log
       fi
       echo "Response check failed, please check the logs in artifacts!"
       exit 1
   else
       echo "Response check succeed!"
   fi

   rm -f ./gmc.opea.io_gmconnectors.yaml ./gmc-manager-rbac.yaml ./gmc-manager.yaml manifests/gmc-router.yaml
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
    init_ChatQnA)
        pushd ChatQnA/kubernetes
        init_chatqna
        popd
        ;;
    install_ChatQnA)
        pushd ChatQnA/kubernetes
        install_chatqna
        popd
        ;;
    validate_ChatQnA)
        pushd ChatQnA/kubernetes
        validate_chatqna
        popd
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
