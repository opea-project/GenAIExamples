# Kubernetes Deployments with gaudi devices
## Prerequisites
- **Kubernetes Cluster**: Access to a Kubernetes v1.29 cluster
 - **CSI Driver**: The K8s cluster must have the CSI driver installed, using the [local-path-provisioner](https://github.com/rancher/local-path-provisioner) with `local_path_provisioner_claim_root` set to `/mnt`. 
 - **Operating System**: Ubuntu 22.04
 - **Gaudi Software Stack**: Verify that your setup uses a valid software stack for Gaudi accelerators, see [Gaudi support matrix](https://docs.habana.ai/en/latest/Support_Matrix/Support_Matrix.html). Note that running LLM on a CPU is possible but will significantly reduce performance.
 - **Gaudi Firmware**:Make sure Firmware is installed on Gaudi nodes. Follow the [Gaudi Firmware Installation](https://docs.habana.ai/en/latest/Installation_Guide/Bare_Metal_Fresh_OS.html#driver-fw-install-bare) guide for detailed instructions.
 - **K8s Plugin for Gaudi**: Install the K8s plugin by following the instructions in [How to install K8s Plugin for Gaudi](https://docs.habana.ai/en/latest/Orchestration/Gaudi_Kubernetes/Device_Plugin_for_Kubernetes.html).
 - **Hugging Face Model Access**: Ensure you have the necessary access to download and use the chosen Hugging Face model. For example, such access is mandatory when using the [Mixtral-8x22B](https://huggingface.co/mistralai/Mixtral-8x22B-Instruct-v0.1).
 - **Helm CLIs installed**
------------

### Deploying the Intel Gaudi base operator on K8S

Install the Operator on a cluster by deploying a Helm chart:

#### Create the Operator namespace
```
kubectl create namespace habana-ai-operator
kubectl label namespace habana-ai-operator pod-security.kubernetes.io/enforce=privileged --overwrite
kubectl label namespace habana-ai-operator pod-security.kubernetes.io/audit=privileged --overwrite
kubectl label namespace habana-ai-operator pod-security.kubernetes.io/warn=privileged --overwrite
```

#### Install Helm chart
```
helm repo add gaudi-helm https://vault.habana.ai/artifactory/api/helm/gaudi-helm
helm repo update
helm install habana-ai-operator gaudi-helm/habana-ai-operator --version 1.18.0-524 -n habana-ai-operator
```
------------
### Kubernetes Deployments steps for each models 
Below steps has the kubernetes deployments which are used for Inference as a service on habana Gaudi . Following are kubectl commands examples for TGI models inference
Make sure to update the HuggingFace token in the yaml files before applying them - HF_TOKEN: "<your-hf-token>"

To delpoy Llama3.1-8B on 1 card
```
kubectl apply -f chatqna-tgi-llama.yml
```
To delpoy Llama3.1-70B 8 cards
```
kubectl apply -f chatqna-tgi-llama70b.yml
```
To deploy text-embeddings-inference
```
kubectl apply -f chatqna-tei.yml
kubectl apply -f chatqna-teirerank.yml
```

------------

## Verify pods and Services

To verify the installation, 
run the command `kubectl get pods -A` to make sure all pods are running.
run the command `kubectl get svc -A` to validate service specific configurations for all the models deployed above

run the below curl command modifying the IP and port respectively to validate the model response
```
curl -k http://<Cluster-IP>:<service-port>/ -X POST -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":32}}' -H 'Content-Type: application/json'
```
------------
## License
The license to use TGI on Habana Gaudi is the one of TGI: https://github.com/huggingface/text-generation-inference/blob/main/LICENSE

Please reach out to api-enterprise@huggingface.co if you have any question.