# Deploy CodeGen in Kubernetes Cluster

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN
>
> You can also customize the "MODEL_ID" if needed.
>
> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the CodeGen workload is running. Otherwise, you need to modify the `codegen.yaml` file to change the `model-volume` to a directory that exists on the node.
> Alternatively, you can change the `codegen.yaml` to use a different type of volume, such as a persistent volume claim.

## Deploy On Xeon

```
cd GenAIExamples/CodeGen/kubernetes/intel/cpu/xeon/manifests
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
export MODEL_ID="meta-llama/CodeLlama-7b-hf"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codegen.yaml
sed -i "s/meta-llama\/CodeLlama-7b-hf/${MODEL_ID}/g" codegen.yaml
kubectl apply -f codegen.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/CodeGen/kubernetes/intel/hpu/gaudi/manifests
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codegen.yaml
kubectl apply -f codegen.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/codegen 7778:7778` to expose the CodeGen service for access.

Open another terminal and run the following command to verify the service if working:

> Note that it may take a couple of minutes for the service to be ready. If the `curl` command below fails, you
> can check the logs of the codegen-tgi pod to see its status or check for errors.

```
kubectl get pods
curl http://localhost:7778/v1/codegen -H "Content-Type: application/json" -d '{
     "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
     }'
```
