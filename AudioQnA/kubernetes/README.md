# Deploy AudioQnA in Kubernetes Cluster on Xeon and Gaudi

This document outlines the deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline components on Intel Xeon server and Gaudi machines.

The AudioQnA Service leverages a Kubernetes operator called genai-microservices-connector(GMC). GMC supports connecting microservices to create pipelines based on the specification in the pipeline yaml file in addition to allowing the user to dynamically control which model is used in a service such as an LLM or embedder. The underlying pipeline language also supports using external services that may be running in public or private cloud elsewhere.

Install GMC  in your Kubernetes cluster, if you have not already done so, by following the steps in Section "Getting Started" at [GMC Install](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector). Soon as we publish images to Docker Hub, at which point no builds will be required, simplifying install.


The AudioQnA application is defined as a Custom Resource (CR) file that the above GMC operator acts  upon. It first checks if the microservices listed in the CR yaml file are running, if not starts them and then proceeds to connect them. When the AudioQnA pipeline is ready, the service endpoint details are returned, letting you use the application. Should you use "kubectl get pods" commands you will see all the component microservices, in particular `asr`, `tts`, and `llm`.


## Using prebuilt images

The AudioQnA uses the below prebuilt images if you choose a Xeon deployment

- tgi-service: ghcr.io/huggingface/text-generation-inference:1.4
- llm: opea/llm-tgi:latest
- asr: opea/asr:latest
- whisper: opea/whisper:latest
- tts: opea/tts:latest
- speecht5: opea/speecht5:latest


Should you desire to use the Gaudi accelerator, two alternate images are used for the embedding and llm services.
For Gaudi:

- tgi-service: ghcr.io/huggingface/tgi-gaudi:1.2.1
- whisper-gaudi: opea/whisper-gaudi:latest
- speecht5-gaudi: opea/speecht5-gaudi:latest

> [NOTE]  
> Please refer to [Xeon README](https://github.com/opea-project/GenAIExamples/blob/main/AudioQnA/docker/xeon/README.md) or [Gaudi README](https://github.com/opea-project/GenAIExamples/blob/main/AudioQnA/docker/gaudi/README.md) to build the OPEA images. These too will be available on Docker Hub soon to simplify use.

## Deploy AudioQnA pipeline
This involves deploying the AudioQnA custom resource. You can use audioQnA_xeon.yaml or if you have a Gaudi cluster, you could use audioQnA_gaudi.yaml. 

1. Create namespace and deploy application
   ```sh
   kubectl create ns audioqa
   kubectl apply -f $(pwd)/audioQnA_xeon.yaml
   ```

2. GMC will reconcile the AudioQnA custom resource and get all related components/services ready. Check if the service up.

   ```sh
   kubectl get service -n audioqa
   ```

3. Retrieve the application access URL

   ```sh
   kubectl get gmconnectors.gmc.opea.io -n audioqa
   NAME      URL                                                    READY   AGE
   audioqa   http://router-service.audioqa.svc.cluster.local:8080   6/0/6   5m
   ```

4. Deploy a client pod to test the application

   ```sh
   kubectl create deployment client-test -n audioqa --image=python:3.8.13 -- sleep infinity
   ```

5. Access the application using the above URL from the client pod

   ```sh
   export CLIENT_POD=$(kubectl get pod -n audioqa -l app=client-test -o jsonpath={.items..metadata.name})
   export accessUrl=$(kubectl get gmc -n audioqa -o jsonpath="{.items[?(@.metadata.name=='audioqa')].status.accessUrl}")
   kubectl exec "$CLIENT_POD" -n audioqa -- curl -s --no-buffer $accessUrl  -X POST  -d '{"byte_str": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "parameters":{"max_new_tokens":64, "do_sample": true, "streaming":false}}' -H 'Content-Type: application/json'
   ```

> [NOTE]

You can remove your AudioQnA pipeline by executing standard Kubernetes kubectl commands to remove a custom resource. Verify it was removed by executing kubectl get pods in the audioqa namespace.
