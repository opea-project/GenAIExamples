#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
USER_ID=$(whoami)
LOG_PATH=/home/$(whoami)/logs
MOUNT_DIR=/home/$USER_ID/.cache/huggingface/hub
IMAGE_REPO=${IMAGE_REPO:-}
CHATQNA_DATAPREP_NAMESPACE="${APP_NAMESPACE}-chatqna-dataprep"

function install_chatqna() {
   # Create namespace APP_NAMESPACE
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

   # Create namespace CHATQNA_DATAPREP_NAMESPACE
   kubectl create ns $CHATQNA_DATAPREP_NAMESPACE
   sed -i "s|namespace: chatqa|namespace: $CHATQNA_DATAPREP_NAMESPACE|g"  ./chatQnA_dataprep_xeon.yaml
   kubectl apply -f ./chatQnA_dataprep_xeon.yaml

   # Wait until the router service is ready
   echo "Waiting for the chatqa-dataprep router service to be ready..."
   wait_until_pod_ready "chatqa-dataprep router" $CHATQNA_DATAPREP_NAMESPACE "router-service"
   output=$(kubectl get pods -n $CHATQNA_DATAPREP_NAMESPACE)
   echo $output

   # Wait until the tgi pod is ready
   TGI_POD_NAME=$(kubectl get pods --namespace=$CHATQNA_DATAPREP_NAMESPACE | grep ^tgi-service | awk '{print $1}')
   kubectl describe pod $TGI_POD_NAME -n $CHATQNA_DATAPREP_NAMESPACE
   kubectl wait --for=condition=ready pod/$TGI_POD_NAME --namespace=$CHATQNA_DATAPREP_NAMESPACE --timeout=300s
}

function validate_chatqna() {
   # deploy client pod for testing
   kubectl create deployment client-test -n $APP_NAMESPACE --image=python:3.8.13 -- sleep infinity

   # wait for client pod ready
   wait_until_pod_ready "client-test" $APP_NAMESPACE "client-test"
   # giving time to populating data

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
   [[ $(grep -c "[DONE]" $LOG_PATH/curl_chatqna.log) != 0 ]]; then
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


function validate_chatqna_dataprep() {
   # deploy client pod for testing
   kubectl create deployment client-test -n $CHATQNA_DATAPREP_NAMESPACE --image=python:3.8.13 -- sleep infinity

   # wait for client pod ready
   wait_until_pod_ready "client-test" $CHATQNA_DATAPREP_NAMESPACE "client-test"
   # giving time to populating data

   kubectl get pods -n $CHATQNA_DATAPREP_NAMESPACE
   # send request to chatqnA
   export CLIENT_POD=$(kubectl get pod -n $CHATQNA_DATAPREP_NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
   echo "$CLIENT_POD"
   accessUrl=$(kubectl get gmc -n $CHATQNA_DATAPREP_NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='chatqa')].status.accessUrl}")
   kubectl exec "$CLIENT_POD" -n $CHATQNA_DATAPREP_NAMESPACE -- curl "$accessUrl/dataprep/ingest"  -X POST  -F 'link_list=["https://raw.githubusercontent.com/opea-project/GenAIInfra/main/microservices-connector/test/data/gaudi.txt"]' -H "Content-Type: multipart/form-data" > $LOG_PATH/curl_dataprep.log
   exit_code=$?
   if [ $exit_code -ne 0 ]; then
       echo "chatqna failed, please check the logs in ${LOG_PATH}!"
       exit 1
   fi

   echo "Checking response results, make sure the output is reasonable. "
   local status=false
   if [[ -f $LOG_PATH/curl_dataprep.log ]] && \
   [[ $(grep -c "Data preparation succeeded" $LOG_PATH/curl_dataprep.log) != 0 ]]; then
       status=true
   fi
   if [ $status == false ]; then
       if [[ -f $LOG_PATH/curl_dataprep.log ]]; then
           cat $LOG_PATH/curl_dataprep.log
       fi
       echo "Response check failed, please check the logs in artifacts!"
       exit 1
   else
       echo "Response check succeed!"
   fi

   kubectl exec "$CLIENT_POD" -n $CHATQNA_DATAPREP_NAMESPACE -- curl $accessUrl  -X POST  -d '{"text":"What are the key features of Intel Gaudi?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json' > $LOG_PATH/curl_chatqna_dataprep.log
   exit_code=$?
   if [ $exit_code -ne 0 ]; then
       echo "chatqna failed, please check the logs in ${LOG_PATH}!"
       exit 1
   fi

   echo "Checking response results, make sure the output is reasonable. "
   local status=false
   if [[ -f $LOG_PATH/curl_chatqna_dataprep.log ]] && \
   [[ $(grep -c "[DONE]" $LOG_PATH/curl_chatqna_dataprep.log) != 0 ]]; then
       status=true
   fi
   if [ $status == false ]; then
       if [[ -f $LOG_PATH/curl_chatqna_dataprep.log ]]; then
           cat $LOG_PATH/curl_chatqna_dataprep.log
       fi
       echo "Response check failed, please check the logs in artifacts!"
       exit 1
   else
       echo "Response check succeed!"
   fi

   rm -f ./gmc.opea.io_gmconnectors.yaml ./gmc-manager-rbac.yaml ./gmc-manager.yaml manifests/gmc-router.yaml
   kubectl delete ns $CHATQNA_DATAPREP_NAMESPACE
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
    install_ChatQnA)
        pushd ChatQnA/kubernetes/gmc
        install_chatqna
        popd
        ;;
    validate_ChatQnA)
        pushd ChatQnA/kubernetes/gmc
        validate_chatqna
        validate_chatqna_dataprep
        popd
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
