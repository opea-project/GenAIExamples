# Deploy Translation in a Kubernetes Cluster

This document outlines the deployment process for a Code Generation (Translation) application that utilizes the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice components on Intel Xeon servers and Gaudi machines.

Please install GMC in your Kubernetes cluster, if you have not already done so, by following the steps in Section "Getting Started" at [GMC Install](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector#readme). We will soon publish images to Docker Hub, at which point no builds will be required, further simplifying install.

If you have only Intel Xeon machines you could use the translation_xeon.yaml file or if you have a Gaudi cluster you could use translation_gaudi.yaml
In the below example we illustrate on Xeon.

## Deploy the RAG application

1. Create the desired namespace if it does not already exist and deploy the application
   ```bash
   export APP_NAMESPACE=CT
   kubectl create ns $APP_NAMESPACE
   sed -i "s|namespace: translation|namespace: $APP_NAMESPACE|g"  ./translation_xeon.yaml
   kubectl apply -f ./translation_xeon.yaml
   ```

2. Check if the application is up and ready
   ```bash
   kubectl get pods -n $APP_NAMESPACE
   ```

3. Deploy a client pod for testing
   ```bash
   kubectl create deployment client-test -n $APP_NAMESPACE --image=python:3.8.13 -- sleep infinity
   ```

4. Check that client pod is ready
   ```bash
    kubectl get pods -n $APP_NAMESPACE
   ```

5. Send request to application
   ```bash
   export CLIENT_POD=$(kubectl get pod -n $APP_NAMESPACE -l app=client-test -o jsonpath={.items..metadata.name})
   export accessUrl=$(kubectl get gmc -n $APP_NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='translation')].status.accessUrl}")
   kubectl exec "$CLIENT_POD" -n $APP_NAMESPACE -- curl -s --no-buffer $accessUrl -X POST -d '{"query":"Translate this from Chinese to English:\nChinese: 我爱机器翻译。\nEnglish:"}' -H 'Content-Type: application/json' > $LOG_PATH/gmc_translation.log
   ```
