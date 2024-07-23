<h1 align="center" id="title">Deploy CodeGen in Kubernetes Cluster</h1>

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN

> You can also customize the "MODEL_ID" if needed.

> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the CodeGEn workload is running. Otherwise, you need to modify the `codegen.yaml` file to change the `model-volume` to a directory that exists on the node.

## Deploy On Xeon

```
cd GenAIExamples/CodeGen/kubernetes/manifests/xeon
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codegen.yaml
kubectl apply -f codegen.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/CodeGen/kubernetes/manifests/gaudi
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codegen.yaml
kubectl apply -f codegen.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/codegen 7778:7778` to expose the CodeGEn service for access.

Open another terminal and run the following command to verify the service if working:

```
kubectl get pods
curl http://localhost:7778/v1/codegen -H "Content-Type: application/json" -d '{
     "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
     }'
```
