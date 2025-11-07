<h1 align="center" id="title">Deploy CodeGen on OpenShift Cluster</h1>

## Prerequisites

1. **Red Hat OpenShift Cluster** with dynamic _StorageClass_ to provision _PersistentVolumes_ e.g. **OpenShift Data Foundation**)
2. Exposed image registry to push there docker images (https://docs.openshift.com/container-platform/4.16/registry/securing-exposing-registry.html).
3. Account on https://huggingface.co/, access to model _ise-uiuc/Magicoder-S-DS-6.7B_ (for Xeon) or _meta-llama/CodeLlama-7b-hf_ (for Gaugi) and token with _Read permissions_. Update the access token in your repository using following commands.

On Xeon:

```
cd GenAIExamples/CodeGen/openshift/manifests/xeon
export HFTOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HFTOKEN}/g" codegen.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift/manifests/gaudi
export HFTOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HFTOKEN}/g" codegen.yaml
```

## Deploy CodeGen

1. Build docker images locally

- LLM Docker Image:

```
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

- MegaService Docker Image:

```
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen
docker build -t opea/codegen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

- UI Docker Image:

```
cd GenAIExamples/CodeGen/ui
docker build -t opea/codegen-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

To verify run the command: `docker images`.

2. Login to docker, tag the images and push it to image registry with following commands:

```
docker login -u <user> -p $(oc whoami -t) <openshift-image-registry_route>
docker tag <image_id> <openshift-image-registry_route>/<namespace>/<image_name>:<tag>
docker push <openshift-image-registry_route>/<namespace>/<image_name>:<tag>
```

To verify run the command: `oc get istag`.

3. Update images names in manifest files.

On Xeon:

```
cd GenAIExamples/CodeGen/openshift/manifests/xeon
export IMAGE_LLM_TGI="YourImage"
export IMAGE_CODEGEN="YourImage"
export IMAGE_CODEGEN_UI="YourImage"
sed -i "s#insert-your-image-llm-tgi#${IMAGE_LLM_TGI}#g" codegen.yaml
sed -i "s#insert-your-image-codegen#${IMAGE_CODEGEN}#g" codegen.yaml
sed -i "s#insert-your-image-codegen-ui#${IMAGE_CODEGEN_UI}#g" ui-server.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift/manifests/gaudi
export IMAGE_LLM_TGI="YourImage"
export IMAGE_CODEGEN="YourImage"
export IMAGE_CODEGEN_UI="YourImage"
sed -i "s#insert-your-image-llm-tgi#${IMAGE_LLM_TGI}#g" codegen.yaml
sed -i "s#insert-your-image-codegen#${IMAGE_CODEGEN}#g" codegen.yaml
sed -i "s#insert-your-image-codegen-ui#${IMAGE_CODEGEN_UI}#g" ui-server.yaml
```

4. Deploy CodeGen with command:

```
oc apply -f codegen.yaml
```

5. Check the _codegen_ route with command `oc get routes` and update the route in _ui-server.yaml_ file.

On Xeon:

```
cd GenAIExamples/CodeGen/openshift/manifests/xeon
export CODEGEN_ROUTE="YourCodegenRoute"
sed -i "s/insert-your-codegen-route/${CODEGEN_ROUTE}/g" ui-server.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift/manifests/gaudi
export CODEGEN_ROUTE="YourCodegenRoute"
sed -i "s/insert-your-codegen-route/${CODEGEN_ROUTE}/g" ui-server.yaml
```

6. Deploy UI with command:

```
oc apply -f ui-server.yaml
```

## Verify Services

Make sure all the pods are running and READY 1/1 (it takes about 5 minutes).

```
oc get pods
curl http://${CODEGEN_ROUTE}/v1/codegen -H "Content-Type: application/json" -d '{
     "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
     }'
```

## Launch the UI

To access the frontend, find the route for _ui-server_ with command `oc get routes` and open it in the browser.
