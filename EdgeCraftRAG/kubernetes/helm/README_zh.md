# EdgeCraft RAG Helm Chart

此文档将为您介绍如何使用Helm chart在Kubernetes集群上部署EdgeCraft RAG (ecrag)。

## 前置条件

- 您需要一个运行中的Kubernetes集群。
- 您需要已经安装Helm。
- 所需的Docker镜像已在您的镜像仓库或本地可用。

## 配置

安装前，请根据您的环境配置 `edgecraftrag/values.yaml` 文件。

### 关键配置

1. **镜像**：设置 `ecrag` 和 `vllm` 的镜像仓库和标签。
   ```yaml
   image:
     ecrag:
       registry: <your-registry>
       tag: <your-tag>
     vllm:
       registry: <your-registry>
       tag: <your-tag>
   ```

2. **环境变量**：配置代理和主机IP。
   ```yaml
   env:
     http_proxy: "http://proxy:port"
     https_proxy: "http://proxy:port"
     HOST_IP: "<node-ip>"
   ```

3. **LLM设置**：调整LLM模型路径和参数。
   ```yaml
   llm:
     LLM_MODEL: "/path/to/model/inside/container" # 确保此路径映射到 paths.model
   ```

4. **持久化路径**：确保主机挂载路径存在。
   ```yaml
   paths:
     model: /home/user/models
     docs: /home/user/docs
   ```

## 安装

请使用如下命令安装helm（以`edgecraftrag`作为发布名为例）：

```bash
cd kubernetes/helm
helm install edgecraftrag ./
```

如果有不同的集群可用，请使用指定的kube config安装chart，例如：

```bash
helm install edgecraftrag ./ --kubeconfig /home/user/.kube/nas.yaml
```

## 验证

### 访问Web界面

服务运行后，您可以通过浏览器访问UI。

1.  **确认端口**：
    查看 `edgecraftrag/values.yaml` 文件中配置的 `nodePort`。这是外部访问端口。

2.  **确认IP**：
    使用部署所运行的Kubernetes节点的IP地址。
    *   如果在本地机器运行（如MicroK8s），使用 `localhost` 或您机器的局域网IP。
    *   如果在远程集群运行，使用该节点的IP。

3.  **在浏览器中打开**：
    访问 `http://<NodeIP>:<NodePort>`
    > 示例：`http://192.168.1.5:31234`

## 卸载

卸载/删除部署的`edgecraftrag`：

```bash
helm uninstall edgecraftrag
```

如果有不同的集群可用，请使用指定的kube config卸载chart，例如：

```bash
helm uninstall edgecraftrag --kubeconfig /home/user/.kube/nas.yaml
```
