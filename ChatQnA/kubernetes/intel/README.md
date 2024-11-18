# Deploy ChatQnA in Kubernetes Cluster

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN
>
> You can also customize the "MODEL_ID" if needed.
>
> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the ChatQnA workload is running. Otherwise, you need to modify the `chatqna.yaml` file to change the `model-volume` to a directory that exists on the node.
>
> File upload size limit: The maximum size for uploaded files is 10GB.

## Deploy On Xeon

```
cd GenAIExamples/ChatQnA/kubernetes/intel/cpu/xeon/manifest
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s|insert-your-huggingface-token-here|${HUGGINGFACEHUB_API_TOKEN}|g" chatqna.yaml
kubectl apply -f chatqna.yaml
```

Newer CPUs such as Intel Cooper Lake, Sapphire Rapids, support [`bfloat16` data type](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format). If you have such CPUs, and given model supports `bfloat16`, adding `--dtype bfloat16` argument for `huggingface/text-generation-inference` server halves its memory usage and speeds it a bit. To use it, run the following commands:

```
# label your node for scheduling the service on it automatically
kubectl label node 'your-node-name' node-type=node-bfloat16

# add `nodeSelector` for the `huggingface/text-generation-inference` server at `chatqna_bf16.yaml`
# create
kubectl apply -f chatqna_bf16.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/ChatQnA/kubernetes/intel/hpu/gaudi/manifest
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s|insert-your-huggingface-token-here|${HUGGINGFACEHUB_API_TOKEN}|g" chatqna.yaml
kubectl apply -f chatqna.yaml
```

## Deploy on Xeon with Remote LLM Model

```
cd GenAIExamples/ChatQnA/kubernetes/intel/cpu/xeon/manifest
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
export vLLM_ENDPOINT="Your Remote Inference Endpoint"
sed -i "s|insert-your-huggingface-token-here|${HUGGINGFACEHUB_API_TOKEN}|g" chatqna-remote-inference.yaml
sed -i "s|insert-your-remote-inference-endpoint|${vLLM_ENDPOINT}|g" chatqna-remote-inference.yaml
```

### Additional Steps for Remote Endpoints with Authentication (If No Authentication Skip This Step)

If your remote inference endpoint is protected with OAuth Client Credentials authentication, update CLIENTID, CLIENT_SECRET and TOKEN_URL with the correct values in "chatqna-llm-uservice-config" ConfigMap



### Deploy
```
kubectl apply -f chatqna-remote-inference.yaml
```

## Deploy on Gaudi with TEI, Rerank, and vLLM Models Running Remotely

```
cd GenAIExamples/ChatQnA/kubernetes/intel/hpu/gaudi/manifest
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
export vLLM_ENDPOINT="Your Remote Inference Endpoint"
export TEI_EMBEDDING_ENDPOINT="Your Remote TEI Embedding Endpoint"
export TEI_RERANKING_ENDPOINT="Your Remote Reranking Endpoint"

sed -i "s|insert-your-huggingface-token-here|${HUGGINGFACEHUB_API_TOKEN}|g" chatqna-vllm-remote-inference.yaml
sed -i "s|insert-your-remote-vllm-inference-endpoint|${vLLM_ENDPOINT}|g" chatqna-vllm-remote-inference.yaml
sed -i "s|insert-your-remote-embedding-endpoint|${TEI_EMBEDDING_ENDPOINT}|g" chatqna-vllm-remote-inference.yaml
sed -i "s|insert-your-remote-reranking-endpoint|${TEI_RERANKING_ENDPOINT}|g" chatqna-vllm-remote-inference.yaml
```

### Additional Steps for Remote Endpoints with Authentication (If No Authentication Skip This Step)

If your remote inference endpoint is protected with OAuth Client Credentials authentication, update CLIENTID, CLIENT_SECRET and TOKEN_URL with the correct values in "chatqna-llm-uservice-config", "chatqna-data-prep-config", "chatqna-embedding-usvc-config", "chatqna-reranking-usvc-config", "chatqna-retriever-usvc-config" ConfigMaps

### Deploy
```
kubectl apply -f chatqna-vllm-remote-inference.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/chatqna 8888:8888` to expose the ChatQnA service for access.

Open another terminal and run the following command to verify the service if working:

```console
curl http://localhost:8888/v1/chatqna \
    -H 'Content-Type: application/json' \
    -d '{"messages": "What is the revenue of Nike in 2023?"}'
```
