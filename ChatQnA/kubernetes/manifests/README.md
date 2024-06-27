<h1 align="center" id="title">Deploy ChatQnA in Kubernetes Cluster on Xeon and Gaudi</h1>
This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline components on Intel Xeon server and Gaudi machines.

The ChatQnA Service leverages a Kubernetes operator called genai-microservices-connector(GMC). GMC supports connecting microservices to create pipelines based on the specification in the pipeline yaml file in addition to allowing the user to dynamically control which model is used in a service such as an LLM or embedder. The underlying pipeline language also supports using external services that may be running in public or private cloud elsewhere.

Please install GMC  in your Kubernetes cluster, if you have not already done so, by following the steps in Section "Getting Started" at [GMC Install](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector). Soon as we publish images to Docker Hub, at which point no builds will be required, simplifying install/


The ChatQnA application is defined as a Custom Resource (CR) file that the above GMC operator acts  upon. It first checks if the microservices listed in the CR yaml file are running, if not starts them and then proceeds to connect them. When the ChatQnA RAG pipeline is ready, the service endpoint details are returned, letting you use the application. Should you use "kubectl get pods" commands you will see all the component microservices, in particular `embedding`, `retriever`, `rerank`, and `llm`.


## Prebuilt images

The ChatQnA uses the below prebuilt images if you choose a Xeon deployment

- redis-vector-db: redis/redis-stack:7.2.0-v9
- tei_embedding_service: ghcr.io/huggingface/text-embeddings-inference:cpu-1.2
- embedding: opea/embedding-tei:latest
- retriever: opea/retriever-redis:latest
- tei_xeon_service: ghcr.io/huggingface/text-embeddings-inference:cpu-1.2
- reranking: opea/reranking-tei:latest
- tgi_service: ghcr.io/huggingface/text-generation-inference:1.4
- llm: opea/llm-tgi:latest
- chaqna-xeon-backend-server: opea/chatqna:latest

Should you desire to use the Gaudi accelerator, two alternate images are used for the embedding and llm services.
For Gaudi:

- tei-embedding-service: opea/tei-gaudi:latest
- tgi-service: ghcr.io/huggingface/tgi-gaudi:1.2.1

> [NOTE]  
> Please refer README [for Xeon](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker/xeon/README.md) and [for Gaudi](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker/gaudi/README.md) to build the opea images. These too will be available on Docker Hub soon.

## Deploy ChatQnA pipeline
This involves deploying the ChatQnA custom resource. You can use chatQnA_xeon.yaml or if you have a Gaudi cluster, you could use chatQnA_gaudi.yaml. 

```sh
kubectl create ns chatqa
kubectl apply -f $(pwd)/chatQnA_xeon.yaml
```

**GMC will reconcile chatQnA custom resource and get all related components/services ready**

```sh
kubectl get service -n chatqa
```

**Check GMC chatQnA custom resource to get access URL for the pipeline**

```bash
$kubectl get gmconnectors.gmc.opea.io -n chatqa
NAME     URL                                                      READY     AGE
chatqa   http://router-service.chatqa.svc.cluster.local:8080      8/0/8     3m
```

**Deploy one client pod for testing the chatQnA application**

```bash
kubectl create deployment client-test -n chatqa --image=python:3.8.13 -- sleep infinity
```

**Access the pipeline using the above URL from the client pod**

```bash
export CLIENT_POD=$(kubectl get pod  -l app=client-test -o jsonpath={.items..metadata.name})
export accessUrl=$(kubectl get gmc -n chatqa -o jsonpath="{.items[?(@.metadata.name=='chatqa')].status.accessUrl}")
kubectl exec "$CLIENT_POD" -n chatqa -- curl $accessUrl  -X POST  -d '{"text":"What is the revenue of Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json'
```

Should you want to change for instance the LLM model you are using in the ChatQnA pipeline, just edit the custom resource file. For instance, if you want to using Llama-2-7b-chat-hf make the following edit.

**Modify chatQnA custom resource to change to another LLM model**

```yaml
- name: Tgi
  internalService:
    serviceName: tgi-svc
    config:
      LLM_MODEL_ID: Llama-2-7b-chat-hf
```

Apply the change using
```
kubectl apply -f $(pwd)/chatQnA_xeon.yaml
```

**Check the tgi-svc-deployment has been changed to use the new LLM Model**

```sh
kubectl get deployment tgi-svc-deployment -n chatqa -o jsonpath="{.spec.template.spec.containers[*].env[?(@.name=='LLM_MODEL_ID')].value}"
```

**Access the updated pipeline using the above URL from the client pod**

```bash
kubectl exec "$CLIENT_POD" -n chatqa -- curl $accessUrl  -X POST  -d '{"text":"What is the revenue of Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json'
```

> [NOTE]

You can remove your ChatQnA pipeline by executing standard Kubernetes kubectl commands to remove a custom resource. Verify it was removed by executing kubectl get pods in the chatqa namespace.
