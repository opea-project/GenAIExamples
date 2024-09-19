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
cd GenAIExamples/ChatQnA/kubernetes/intel/cpu/xeon/manifests
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" chatqna.yaml
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
cd GenAIExamples/ChatQnA/kubernetes/intel/hpu/gaudi/manifests
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" chatqna.yaml
kubectl apply -f chatqna.yaml
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
