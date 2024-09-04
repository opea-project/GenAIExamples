# Deploy CodeTrans in Kubernetes Cluster

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN

> You can also customize the "MODEL_ID" if needed.

> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the CodeTrans workload is running. Otherwise, you need to modify the `codetrans.yaml` file to change the `model-volume` to a directory that exists on the node.

## Required Models

By default, the LLM model is set to a default value as listed below:

|Service  |Model                    |
|---------|-------------------------|
|LLM      |HuggingFaceH4/mistral-7b-grok|

Change the `MODEL_ID` in `codetrans.yaml` for your needs.

## Deploy On Xeon

```bash
cd GenAIExamples/CodeTrans/kubernetes/manifests/xeon
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codetrans.yaml
kubectl apply -f codetrans.yaml
```

## Deploy On Gaudi

```bash
cd GenAIExamples/CodeTrans/kubernetes/manifests/gaudi
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" codetrans.yaml
kubectl apply -f codetrans.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/codetrans 7777:7777` to expose the CodeTrans service for access.

Open another terminal and run the following command to verify the service if working:

```bash
curl http://localhost:7777/v1/codetrans \
    -H 'Content-Type: application/json' \
    -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
```

To consume the service using nginx, run the command below. The `${host_ip}` is the external ip of your server.

```bash
curl http://${host_ip}:30789/v1/codetrans \
    -H 'Content-Type: application/json' \
    -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
```
