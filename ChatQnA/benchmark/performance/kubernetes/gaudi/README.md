## Table of Contents

- [Deployment](#deployment)
  - [Prerequisites](#prerequisites)
  - [Deployment Scenarios](#deployment-scenarios)
    - [1. Deploy with Gaudi Devices](#1-deploy-with-gaudi-devices)
    - [2. Deploy with Multiple Pod Instances](#2-deploy-with-multiple-pod-instances)
    - [3. Deploy with a Specific Namespace](#3-deploy-with-a-specific-namespace)
    - [4. Deploy with Proxy](#4-deploy-with-proxy)
  - [Teardown](#teardown)
- [Benchmark](#benchmark)

## Deployment

### Prerequisites

- Kubernetes installation: Use [kubespray](https://github.com/opea-project/docs/blob/main/guide/installation/k8s_install/k8s_install_kubespray.md) or other official Kubernetes installation guides.
- Helm installation: Follow the [Helm documentation](https://helm.sh/docs/intro/install/#helm) to install Helm.
- Install the OPEA Helm Chart:

  ```bash
  helm repo add opea https://opea-project.github.io/GenAIInfra
  ```
- Setup Hugging Face Token
  To access models and APIs from Hugging Face, set your token as environment variable.
  ```bash
  export HFTOKEN="insert-your-huggingface-token-here"
  ```

### Deployment Scenarios

#### 1. Deploy with Gaudi Devices

To offload TEI embedding and TGI inference to Intel Gaudi devices, use the specific values file.

```bash
# Extract chart contents to access provided configuration files.
helm pull opea/chatqna --untar

# Deploy using the Gaudi-specific configuration.
helm install chatqna opea/chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f chatqna/gaudi-values.yaml 

# List the runtime names of the deployed kubernetes services
kubectl get svc

# Check the status of pods and ensure they are ready before proceeding
kubectl get pods

```

#### 2. Deploy with Multiple Pod Instances

To effectively deploy your workload across multiple nodes, follow these steps.

##### Preload Shared Models
Downloading models simultaneously to multiple nodes in your cluster can overload resources such as network bandwidth, memory and storage. To prevent resource exhaustion, it's recommended to preload the models in advance.

```bash
pip install -U "huggingface_hub[cli]"
sudo mkdir -p /mnt/models
sudo chmod 777 /mnt/models
huggingface-cli download --cache-dir /mnt/models Intel/neural-chat-7b-v3-3
export MODELDIR=/mnt/models
```
Once the models are downloaded, you can consider the following methods for sharing them across nodes:
- Persistent Volume Claim (PVC): This is the recommended approach for production setups. For more details on using PVC, refer to [PVC](https://github.com/opea-project/GenAIInfra/blob/main/helm-charts/README.md#using-persistent-volume).
- Local Host Path: For simpler testing, ensure that each node involved in the deployment follows the steps above to locally prepare the models. After preparing the models, use `--set global.modelUseHostPath=${MODELDIR}` in the deployment command.


##### Configure Multiple Pod Instances

To deploy the workload with multiple pod instances, modify the [cluster.yaml](./baseline/cluster.yaml) configuration file. For clusters with multiple nodes, you can uncomment the `evenly_distributed: true` option to ensure pods are distributed envely across nodes. If you prefer to deploy to specific nodes, uncomment the `affinity` section and specify the target node names, which can be obtained using `kubectl get nodes --show-lables`.

Ensure you use the chart-defined service names for proper configuration. These names correspond to the logical services defined in the Helm chart, such as `retriever-usvc`, `tei`, and `tgi`. You can view the full list of service names by running `helm show readme opea/chatqna`.

```
# cluster.yaml - Example configuration for multiple instances
tgi:                          # Chart-defined service name
  replicaCount: 15            # Number of pod instances to deploy (default is 1 if not specified)
  evenly_distributed: true    # Distribute instances evenly across hardware nodes
  affinity:                   # Schedule pods on specific nodes
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                  - node1     # Node name
                  - node2
```

##### Deploy with Your Custom Configuration
Use the following command to deploy the workload with multiple instances:

```bash
helm install chatqna opea/chatqna \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  --set global.modelUseHostPath=${MODELDIR} \
  -f chatqna/gaudi-values.yaml -f cluster.yaml
```

##### Deploy with Your Custom Configuration
The default deployment includes the rerank service. If you prefer not to use rerank, you can deploy using [cluster_no_rerank.yaml](./cluster_no_rerank.yaml) configuration file.

```bash
helm install chatqna opea/chatqna \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  --set global.modelUseHostPath=${MODELDIR} \
  -f chatqna/gaudi-values.yaml -f cluster.yaml \
  -f cluster_no_rerank.yaml
```

#### 3. Deploy with a Specific Namespace

To deploy the workload in a specific namespace:

```bash
export NAMESPACE=“insert-your-workload-namespace”
helm install chatqna opea/chatqna \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  -f chatqna/gaudi-values.yaml \
  --namespace ${NAMESPACE} --create-namespace
```

When using a custom namespace, remember to specify it when interacting with Kubernetes:

```bash
kubectl get pods -n ${NAMESPACE}
```

#### 4. Deploy with Proxy

If your environment requires proxy settings:

```bash
helm install chatqna opea/chatqna \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  --set global.http_proxy=${http_proxy} \
  --set global.https_proxy=${https_proxy} \
  -f chatqna/gaudi-values.yaml
```

### Teardown

Uninstall `opea/chatqna` chart when it's no longer needed.
 
```bash
helm uninstall chatqna
```

## Benchmark

To benchmark the deployed `opea/chatqna`, refer to the [GenAIEval](https://github.com/opea-project/GenAIEval) repository and the [benchmark](https://github.com/opea-project/GenAIEval/tree/main/evals/benchmark) page to set up the benchmarking tools. Adjust the the parameters in [benchmark.yaml](benchmark.yaml) and place it in the same directory as [benchmark.py](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/benchmark.py). Then run the benchmark using the following command:

```bash
python benchmark.py
```
