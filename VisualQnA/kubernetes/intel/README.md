# Deploy VisualQnA in Kubernetes Cluster

> [NOTE]
> You can also customize the "LVM_MODEL_ID" if needed.
>
> You need to make sure you have created the directory `/mnt/opea-models` to save the cached model on the node where the visualqna workload is running. Otherwise, you need to modify the `visualqna.yaml` file to change the `model-volume` to a directory that exists on the node.

## Deploy On Xeon

```
cd GenAIExamples/visualqna/kubernetes/manifests/xeon
kubectl apply -f visualqna.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/visualqna/kubernetes/manifests/gaudi
kubectl apply -f visualqna.yaml
```

## Verify Services

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Then run the command `kubectl port-forward svc/visualqna 8888:8888` to expose the visualqna service for access.

Open another terminal and run the following command to verify the service if working:

```console
curl http://localhost:8888/v1/visualqna \
    -H 'Content-Type: application/json' \
    -d '{"messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What'\''s in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://www.ilankelman.org/stopsigns/australia.jpg"
            }
          }
        ]
      }
    ],
    "max_tokens": 128}'
```
