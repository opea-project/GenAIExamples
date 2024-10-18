<h1 align="center" id="title">Deploy ChatQnA on OpenShift Cluster</h1>

## Prerequisites

1. **Red Hat OpenShift Cluster** with dynamic _StorageClass_ to provision _PersistentVolumes_ e.g. **OpenShift Data Foundation**)
2. Exposed image registry to push the docker images (https://docs.openshift.com/container-platform/4.16/registry/securing-exposing-registry.html).
3. (Optional) Create a new OpenShift project for ChatQnA resources:
   ```
   export PROJECT="YourOwnProject"
   oc new-project ${PROJECT}
   ```
4. Access to https://huggingface.co/ to get access token with _Read_ permissions. Also, get the LangChain API key. Update the access token and the key in your repository:
   ```
   cd GenAIExamples/ChatQnA/openshift/manifests/xeon
   export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
   export LANGCHAIN_API_KEY="YourOwnKey"
   export PROJECT="YourOwnProject"
   sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" chatqna.yaml
   sed -i "s/insert-your-langchain-key-here/${LANGCHAIN_API_KEY}/g" chatqna.yaml
   sed -i "s/insert-your-namespace-here/${PROJECT}/g" chatqna.yaml
   ```
   You can also customize the "MODEL_ID" and "model-volume".

## Deploy ChatQnA On Xeon

1. Build docker images locally \
    Start with cloning the repo:

   ```bash
   git clone https://github.com/opea-project/GenAIComps.git
   cd GenAIComps
   ```

   - Build Embedding Image

   ```bash
   docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
   ```

   - Build Retriever Image

   ```bash
   docker build --no-cache -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./comps/retrievers/langchain/redis/docker/Dockerfile .
   ```

   - Build Rerank Image

   ```bash
   docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./comps/reranks/langchain-mosec/docker/Dockerfile .
   ```

   - Build LLM Image \
     Use TGI as the backend:

   ```bash
   docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
   ```

   - Build Dataprep Image

   ```bash
   docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
   cd ..
   ```

   - Build MegaService Docker Image

   To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via the below command:

   ```bash
   git clone https://github.com/opea-project/GenAIExamples.git
   cd GenAIExamples/ChatQnA/docker
   docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
   cd ../../..
   ```

   To verify run `docker images` command and you should have the following container images:

   - `opea/chatqna:latest`
   - `opea/dataprep-redis:latest`
   - `opea/embedding-tei:latest`
   - `opea/llm-tgi:latest`
   - `opea/reranking-tei:latest`
   - `opea/retriever-redis:latest`

2. Log in to Podman, tag the images, and push them to the image registry with the following commands:

   ```
   podman login -u <user> -p $(oc whoami -t) <openshift-image-registry_route> --tls-verify=false
   podman tag <image_id> <openshift-image-registry_route>/<project>/<image_name>:<tag>
   podman push <openshift-image-registry_route>/<project>/<image_name>:<tag>
   ```

   To verify run the command: `oc get istag`.

3. Deploy ChatQnA with command:
   ```
   oc apply -f chatqna.yaml
   ```

## Verify Services

Ensure all the pods are running, and restart the chatqna-xxxx pod if necessary.

Check ChatQnA route:

```
oc get route
```

Use `HOST/PORT` field from the output to populate `YourChatqnaRoute` below and execute the command:

```
oc get pods
export CHATQNA_ROUTE="YourChatqnaRoute"
curl http://${CHATQNA_ROUTE}/v1/chatqna -H "Content-Type: application/json" -d '{
     "messages": "What is Intel Corporation?"
     }'
```
