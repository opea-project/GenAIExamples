# Deploy Translation in Kubernetes Cluster

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN
>
> You can also customize the "MODEL_ID" if needed.
>
> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the Translation workload is running. Otherwise, you need to modify the `translation.yaml` file to change the `model-volume` to a directory that exists on the node.

## Deploy On Xeon

```
cd GenAIExamples/Translation/kubernetes/intel/cpu/xeon/manifests
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" translation.yaml
kubectl apply -f translation.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/Translation/kubernetes/intel/hpu/gaudi/manifests
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" translation.yaml
kubectl apply -f translation.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/translation 8888:8888` to expose the Translation service for access.

Open another terminal and run the following command to verify the service if working:

```console
curl http://localhost:8888/v1/translation \
    -H 'Content-Type: application/json' \
    -d '{"language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'
```
