# EdgeCraft RAG Helm Chart

This doc intrudoces the Helm chart for deploying EdgeCraft RAG (ecrag) on a Kubernetes cluster.

## Prerequisites

- A running Kubernetes cluster.
- Helm installed.
- Required Docker images available in your registry or locally.

## Configuration

Before installing, you should configure the `edgecraftrag/values.yaml` file according to your environment.

### Key Configurations

1. **Images**: Set the registry and tag for `ecrag` and `vllm`.
   ```yaml
   image:
     ecrag:
       registry: <your-registry>
       tag: <your-tag>
     vllm:
       registry: <your-registry>
       tag: <your-tag>
   ```

2. **Environment Variables**: Configure proxies and host IP.
   ```yaml
   env:
     http_proxy: "http://proxy:port"
     https_proxy: "http://proxy:port"
     HOST_IP: "<node-ip>"
   ```

3. **LLM Settings**: Adjust LLM model paths and parameters.
   ```yaml
   llm:
     LLM_MODEL: "/path/to/model/inside/container" # Ensure this maps to paths.model
   ```

4. **Persistent Paths**: Ensure the host paths exist for mounting.
   ```yaml
   paths:
     model: /home/user/models
     docs: /home/user/docs
   ```

## Installation

To install the chart, please use below command (`edgecraftrag` as an example)

```bash
cd kubernetes/helm
helm install edgecraftrag ./edgecraftrag
```

If there're different clusters available, please install the chart with specific kube config, e.g. :

```bash
helm install edgecraftrag ./edgecraftrag --kubeconfig /home/user/.kube/nas.yaml
```

## Verification

### Accessing the Web UI

Once the service is running, you can access the UI via your browser.

1.  **Identify the Port**:
    Check the `nodePort` configured in the `edgecraftrag/values.yaml` file. This is the external access port.

2.  **Identify the IP**:
    Use the IP address of the Kubernetes node where the deployment is running.
    *   If running on your local machine (e.g., MicroK8s), use `localhost` or your machine's LAN IP.
    *   If running on a remote cluster, use that node's IP.

3.  **Open in Browser**:
    Navigate to `http://<NodeIP>:<NodePort>`
    > Example: `http://192.168.1.5:31234`

## Uninstallation

To uninstall/delete the `edgecraftrag` deployment:

```bash
helm uninstall edgecraftrag
```

If there're different clusters available, please uninstall the chart with specific kube config, e.g. :

```bash
helm uninstall edgecraftrag --kubeconfig /home/user/.kube/nas.yaml
```
