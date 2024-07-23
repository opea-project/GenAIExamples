<h1 align="center" id="title">Deploy DocSum in Kubernetes Cluster</h1>

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN

> You can also customize the "MODEL_ID" if needed.

> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the DocSum workload is running. Otherwise, you need to modify the `docsum.yaml` file to change the `model-volume` to a directory that exists on the node.

## Deploy On Xeon

```
cd GenAIExamples/DocSum/kubernetes/manifests/xeon
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" docsum.yaml
kubectl apply -f docsum.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/DocSum/kubernetes/manifests/gaudi
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" docsum.yaml
kubectl apply -f docsum.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/docsum 8888:8888` to expose the DocSum service for access.

Open another terminal and run the following command to verify the service if working:

```console
curl http://localhost:8888/v1/docsum \
    -H 'Content-Type: application/json' \
    -d '{"messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
```
