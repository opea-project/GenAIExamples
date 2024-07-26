# Deploy CodeTrans in Kubernetes Cluster

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN

> You can also customize the "MODEL_ID" if needed.

> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the CodeTrans workload is running. Otherwise, you need to modify the `codetrans.yaml` file to change the `model-volume` to a directory that exists on the node.

## Deploy On Xeon

```
cd GenAIExamples/CodeTrans/kubernetes/manifests/xeon
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codetrans.yaml
kubectl apply -f codetrans.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/CodeTrans/kubernetes/manifests/gaudi
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codetrans.yaml
kubectl apply -f codetrans.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/docsum 8888:8888` to expose the CodeTrans service for access.

Open another terminal and run the following command to verify the service if working:

```console
curl http://localhost:7777/v1/codetrans \
    -H 'Content-Type: application/json' \
    -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
```
