# Deploy SearchQnA in a Kubernetes Cluster

This document outlines the deployment process for a Code Generation (SearchQnA) application that utilizes the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice components on Intel Xeon servers and Gaudi machines.

Install GMC in your Kubernetes cluster, if you have not already done so, by following the steps in Section "Getting Started" at [GMC Install](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector#readme). We will soon publish images to Docker Hub, at which point no builds will be required, further simplifying install.

If you have only Intel Xeon machines you could use the searchQnA_xeon.yaml file or if you have a Gaudi cluster you could use searchQnA_gaudi.yaml
In the below example we illustrate on Xeon.

## Deploy the RAG application

1. Create the desired namespace if it does not already exist and deploy the application
   ```bash
   export APP_NAMESPACE=CT
   kubectl create ns $APP_NAMESPACE
   sed -i "s|namespace: searchqa|namespace: $APP_NAMESPACE|g"  ./searchQnA_xeon.yaml
   sed -i "s|insert-your-google-api-key-here|$GOOGLE_API_KEY|g"  ./searchQnA_xeon.yaml
   sed -i "s|insert-your-google-cse-id-here|$GOOGLE_CSE_ID|g"  ./searchQnA_xeon.yaml
   kubectl apply -f ./searchQnA_xeon.yaml
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
   export accessUrl=$(kubectl get gmc -n $APP_NAMESPACE -o jsonpath="{.items[?(@.metadata.name=='searchqa')].status.accessUrl}")
   kubectl exec "$CLIENT_POD" -n $APP_NAMESPACE -- curl -s --no-buffer $accessUrl -X POST -d '{"text":"What is the latest news? Give me also the source link."}' -H 'Content-Type: application/json' > $LOG_PATH/gmc_searchqa.log
   ```
