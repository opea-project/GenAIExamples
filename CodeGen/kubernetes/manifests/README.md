<h1 align="center" id="title">Deploy CodeGen in Kubernetes Cluster</h1>

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN
> You can also customize the "MODEL_ID" and "model-volume"

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

Make sure all the pods are running, and restart the codegen-xxxx pod if necessary.

```
kubectl get pods
curl http://codegen:6666/v1/codegen -H "Content-Type: application/json" -d '{
     "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
     }'
```
