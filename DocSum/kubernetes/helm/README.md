# Deploy DocSum on Kubernetes cluster

- You should have Helm (version >= 3.15) installed. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.
- For more deploy options, refer to [helm charts README](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts#readme).

## Deploy on Xeon

```
export HFTOKEN="insert-your-huggingface-token-here"
helm install docsum oci://ghcr.io/opea-project/charts/docsum  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f cpu-values.yaml
```

## Deploy on Gaudi

```
export HFTOKEN="insert-your-huggingface-token-here"
helm install docsum oci://ghcr.io/opea-project/charts/docsum  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f gaudi-values.yaml
```

## Deploy on AMD ROCm using Helm charts from the binary Helm repository

```bash
mkdir ~/docsum-k8s-install && cd ~/docsum-k8s-install
```

### Cloning repos

```bash
git clone git clone https://github.com/opea-project/GenAIExamples.git
```

### Go to the installation directory

```bash
cd GenAIExamples/DocSum/kubernetes/helm
```

### Settings system variables

```bash
export HFTOKEN="your_huggingface_token"
export MODELDIR="/mnt/opea-models"
export MODELNAME="Intel/neural-chat-7b-v3-3"
```

### Setting variables in Values files

#### If ROCm vLLM used
```bash
nano ~/docsum-k8s-install/GenAIExamples/DocSum/kubernetes/helm/rocm-values.yaml
```

- HIP_VISIBLE_DEVICES - this variable specifies the ID of the GPU that you want to use.
  You can specify either one or several comma-separated ones - "0" or "0,1,2,3"
- TENSOR_PARALLEL_SIZE - must match the number of GPUs used
- resources:
  limits:
  amd.com/gpu: "1" - replace "1" with the number of GPUs used

#### If ROCm TGI used

```bash
nano ~/docsum-k8s-install/GenAIExamples/DocSum/kubernetes/helm/rocm-tgi-values.yaml
```

- HIP_VISIBLE_DEVICES - this variable specifies the ID of the GPU that you want to use.
  You can specify either one or several comma-separated ones - "0" or "0,1,2,3"
- extraCmdArgs: [ "--num-shard","1" ] - replace "1" with the number of GPUs used
- resources:
  limits:
  amd.com/gpu: "1" - replace "1" with the number of GPUs used

### Installing the Helm Chart

#### If ROCm vLLM used
```bash
helm upgrade --install docsum oci://ghcr.io/opea-project/charts/docsum \
    --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
    --values rocm-values.yaml
```

#### If ROCm TGI used
```bash
helm upgrade --install docsum oci://ghcr.io/opea-project/charts/docsum \
    --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
    --values rocm-tgi-values.yaml
```

## Deploy on AMD ROCm using Helm charts from Git repositories

### Creating working dirs

```bash
mkdir ~/docsum-k8s-install && cd ~/docsum-k8s-install
```

### Cloning repos

```bash
git clone git clone https://github.com/opea-project/GenAIExamples.git
git clone git clone https://github.com/opea-project/GenAIInfra.git
```

### Go to the installation directory

```bash
cd GenAIExamples/DocSum/kubernetes/helm
```

### Settings system variables

```bash
export HFTOKEN="your_huggingface_token"
export MODELDIR="/mnt/opea-models"
export MODELNAME="Intel/neural-chat-7b-v3-3"
```

### Setting variables in Values files

#### If ROCm vLLM used
```bash
nano ~/docsum-k8s-install/GenAIExamples/DocSum/kubernetes/helm/rocm-values.yaml
```

- HIP_VISIBLE_DEVICES - this variable specifies the ID of the GPU that you want to use. 
You can specify either one or several comma-separated ones - "0" or "0,1,2,3"
- TENSOR_PARALLEL_SIZE - must match the number of GPUs used
- resources:
    limits:
      amd.com/gpu: "1" - replace "1" with the number of GPUs used

#### If ROCm TGI used

```bash
nano ~/docsum-k8s-install/GenAIExamples/DocSum/kubernetes/helm/rocm-tgi-values.yaml
```

- HIP_VISIBLE_DEVICES - this variable specifies the ID of the GPU that you want to use.
  You can specify either one or several comma-separated ones - "0" or "0,1,2,3"
- extraCmdArgs: [ "--num-shard","1" ] - replace "1" with the number of GPUs used
- resources:
    limits:
      amd.com/gpu: "1" - replace "1" with the number of GPUs used

### Installing the Helm Chart

#### If ROCm vLLM used
```bash
cd ~/docsum-k8s-install/GenAIInfra/helm-charts
./update_dependency.sh
helm dependency update docsum
helm upgrade --install docsum docsum \
    --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
    --values ../../GenAIExamples/DocSum/kubernetes/helm/rocm-values.yaml
```

#### If ROCm TGI used
```bash
cd ~/docsum-k8s-install/GenAIInfra/helm-charts
./update_dependency.sh
helm dependency update docsum
helm upgrade --install docsum docsum \
    --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
    --values ../../GenAIExamples/DocSum/kubernetes/helm/rocm-tgi-values.yaml
```
