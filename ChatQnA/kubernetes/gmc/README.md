# Deploy ChatQnA in Kubernetes Cluster on Xeon and Gaudi

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline components on Intel Xeon server and Gaudi machines.

The ChatQnA Service leverages a Kubernetes operator called genai-microservices-connector (GMC). GMC supports connecting microservices to create pipelines based on the specification in the pipeline yaml file in addition to allowing the user to dynamically control which model is used in a service such as an LLM or embedder. The underlying pipeline language also supports using external services that may be running in public or private cloud elsewhere.

Install GMC  in your Kubernetes cluster, if you have not already done so, by following the steps in Section "Getting Started" at [GMC Install](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector/README.md). Soon as we publish images to Docker Hub, at which point no builds will be required, simplifying install.


The ChatQnA application is defined as a Custom Resource (CR) file that the above GMC operator acts  upon. It first checks if the microservices listed in the CR yaml file are running, if not starts them and then proceeds to connect them. When the ChatQnA RAG pipeline is ready, the service endpoint details are returned, letting you use the application. Should you use "kubectl get pods" commands you will see all the component microservices, in particular `embedding`, `retriever`, `rerank`, and `llm`.


## Using prebuilt images

The ChatQnA uses the below prebuilt images if you choose a Xeon deployment

- redis-vector-db: redis/redis-stack:7.2.0-v9
- tei_embedding_service: ghcr.io/huggingface/text-embeddings-inference:cpu-1.6
- retriever: opea/retriever:latest
- tei_xeon_service: ghcr.io/huggingface/text-embeddings-inference:cpu-1.6
- tgi-service: ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu
- chaqna-xeon-backend-server: opea/chatqna:latest

Should you desire to use the Gaudi accelerator, two alternate images are used for the embedding and llm services.
For Gaudi:

tei-embedding-service: ghcr.io/huggingface/text-embeddings-inference:hpu-1.7
tgi-service: gghcr.io/huggingface/tgi-gaudi:2.3.1


> [NOTE]  
> Please refer to [Xeon README](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker_compose/intel/cpu/xeon/README.md) or [Gaudi README](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker_compose/intel/hpu/gaudi/README.md) to build the OPEA images. These too will be available on Docker Hub soon to simplify use.

## Deploy ChatQnA pipeline
This involves deploying the ChatQnA custom resource. You can use chatQnA_xeon.yaml or if you have a Gaudi cluster, you could use chatQnA_gaudi.yaml. 

1. Create namespace and deploy application
   ```sh
   kubectl create ns chatqa
   kubectl apply -f $(pwd)/chatQnA_xeon.yaml
   ```

2. GMC will reconcile the ChatQnA custom resource and get all related components/services ready. Check if the service up.

   ```sh
   kubectl get service -n chatqa
   ```

3. Retrieve the application access URL

   ```sh
   kubectl get gmconnectors.gmc.opea.io -n chatqa
   NAME     URL                                                      READY     AGE
   chatqa   http://router-service.chatqa.svc.cluster.local:8080      8/0/8     3m
   ```

4. Deploy a client pod to test the application

   ```sh
   kubectl create deployment client-test -n chatqa --image=python:3.8.13 -- sleep infinity
   ```

5. Access the application using the above URL from the client pod

   ```sh
   export CLIENT_POD=$(kubectl get pod -n chatqa -l app=client-test -o jsonpath={.items..metadata.name})
   export accessUrl=$(kubectl get gmc -n chatqa -o jsonpath="{.items[?(@.metadata.name=='chatqa')].status.accessUrl}")
   kubectl exec "$CLIENT_POD" -n chatqa -- curl -s --no-buffer $accessUrl  -X POST  -d '{"text":"What is the revenue of Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json'
   ```

6. Perhaps you want to try another LLM model? Just modify the application custom resource to use another LLM model

   Should you, for instance, want to change the LLM model you are using in the ChatQnA pipeline, just edit the custom resource file.
   For example, to use Llama-2-7b-chat-hf make the following edit:


   ```yaml
   - name: Tgi
     internalService:
       serviceName: tgi-service-m
       config:
         LLM_MODEL_ID: Llama-2-7b-chat-hf
   ```

7. Apply the change
   ```
   kubectl apply -f $(pwd)/chatQnA_xeon.yaml
   ```

8. Check that the tgi-svc-deployment has been changed to use the new LLM Model

   ```sh
   kubectl get deployment tgi-service-m-deployment -n chatqa -o jsonpath="{.spec.template.spec.containers[*].env[?(@.name=='LLM_MODEL_ID')].value}"
   ```

9. Access the updated pipeline using the same URL from above using the client pod

   ```sh
   kubectl exec "$CLIENT_POD" -n chatqa -- curl -s --no-buffer $accessUrl -X POST -d '{"text":"What is the revenue of Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json'
   ```

> [NOTE]

You can remove your ChatQnA pipeline by executing standard Kubernetes kubectl commands to remove a custom resource. Verify it was removed by executing kubectl get pods in the chatqa namespace.
