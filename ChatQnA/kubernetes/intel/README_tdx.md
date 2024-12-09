# Deploy example application in Kubernetes Cluster on Xeon with Intel TDX

This document outlines the deployment process for an example application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline components on Intel Xeon server where the microservices are protected by [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html).

The deployment process is intended for users who want to deploy an example application:

- with pods protected by Intel TDX,
- on a single node in a cluster (acting as a master and worker) that is a Xeon 5th Gen platform or later,
- running Ubuntu 24.04,
- using images pushed to public repository, like quay.io or docker hub.

It's split into 3 sections:

1. [Cluster Configuration](#cluster-configuration) - steps required to prepare components in the cluster required to use Intel TDX.
2. [Node configuration](#node-configuration) - additional steps to be performed on the node that are required to run heavy applications like OPEA ChatQnA.
3. [Deployment of services protected with Intel TDX](#deployment-of-services-protected-with-intel-tdx) - describes how to deploy an example application with services protected using Intel TDX.

> [!NOTE]
> Running TDX-protected services requires the user to define the pod's resources request (cpu, memory).
>
> Due to lack of hotplugging feature in TDX, the assigned resources cannot be changed after the pod is scheduled and the resources will not be shared with any other pod.
>
> This means, that the total amount of resources assigned to all TDX-protected pods must be less than the total amount of resources available on the node, leaving room for the non-TDX pods requests.


## Cluster Configuration

To prepare cluster to run Intel TDX-protected workloads, follow [Intel Confidential Computing Documentation](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/01/introduction/index.html).


## Node Configuration

This section outlines required changes to be performed on each node.
These steps might be automated with various configuration management tools like Ansible, Puppet, Chef, etc.


### Kubelet Configuration

To run a complex and heavy application like OPEA, the cluster administrator must increase the kubelet timeout for container creation, otherwise the pod creation may fail due to timeout `Context deadline exceeded`.
This is required because the container creation process can take a long time due to the size of pod images and the need to download the AI models.
Run the following script on all nodes to increase the kubelet timeout to 30 minutes and restart the kubelet automatically if the setting was applied (sudo required):

```bash
echo "Setting up the environment..."
kubelet_config="/var/lib/kubelet/config.yaml"
# save the current kubelet timeout setting
previous=$(sudo grep runtimeRequestTimeout "${kubelet_config}")
# Increase kubelet timeout
sudo sed -i 's/runtimeRequestTimeout: .*/runtimeRequestTimeout: 30m/' "${kubelet_config}"
new=$(sudo grep runtimeRequestTimeout "${kubelet_config}")
# Check if the kubelet timeout setting was updated
if [[ "$previous" == "$new" ]]; then
  echo "kubelet runtimeRequestTimeout setting was not updated."
else
  echo "kubelet runtimeRequestTimeout setting was updated."
  echo "Updated kubelet runtimeRequestTimeout setting:"
  sudo grep runtimeRequestTimeout "${kubelet_config}"
  echo "Restarting kubelet..."
  sudo systemctl daemon-reload && sudo systemctl restart kubelet
  echo "Waiting 30s for kubelet to restart..."
  sleep 30
  echo "kubelet restarted."
fi
```

> [!NOTE]
> The script is prepared for vanilla kubernetes installation.
> If you are using a different kubernetes distribution, the kubelet configuration file location may differ or the setting could be managed otherwise.
>
> After kubelet restart, some of the internal pods from `kube-system` namespace might be reloaded automatically.

All kubelet configuration options can be found [here](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/).


## Deployment of services protected with Intel TDX

This section describes how to deploy an example application with services protected using Intel TDX:

1. [Overview of the changes needed](#overview-of-the-changes-needed) - describes the changes required to protect a single component with Intel TDX.
2. [Example deployment of ChatQnA with TDX protection](#example-deployment-of-chatqna-with-tdx-protection) - provides a quick start to run ChatQnA example application with all services protected with Intel TDX.
3. [Customization of deployment configuration](#customization-of-deployment-configuration) - describes how to manually modify the deployment configuration to protect a single component with Intel TDX.


### Overview of the changes needed

To protect a single component with Intel TDX, user must modify its manifest file.
The process is described in details in the [Demo Workload Deployment](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/03/demo_workload_deployment/#pod-isolated-by-kata-containers-protected-with-intel-tdx-and-quote-verified-using-intel-trust-authority).

Here, we describe the required changes on the example Deployment definition below:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-uservice
  #  (...)
spec:
  selector:
      matchLabels:
         app.kubernetes.io/name: llm-uservice
         app.kubernetes.io/instance: llm-uservice
  #  (...)
  template:
    metadata:
      # (...)
      annotations:
        io.katacontainers.config.runtime.create_container_timeout: "600" # <<--- increase the timeout for container creation
    spec:
      runtimeClassName: kata-qemu-tdx # <<--- this is required to start the pod in Trust Domain (TD, virtual machine protected with Intel TDX)
      containers:
        - name: llm-uservice
          # (...)
          resources: # <<--- specify resources enough to run the service efficiently (memory must be at least 2x the image size)
            limits:
              cpu: "4"
              memory: 4Gi
            requests:
              cpu: "4"
              memory: 4Gi
```


### Example deployment of ChatQnA with TDX protection

As an example we will use the ChatQnA application.
If you want to just give it a try, simply run:

```bash
kubectl apply -f chatqna_tdx.yaml
```

After a few minutes, the ChatQnA services should be up and running in the cluster and all of them will be protected with Intel TDX.
You may verify, that the pods are running with the TDX-protection by checking the runtime class name, e.g.:

```bash
POD_NAME=$(kubectl get pods | grep 'chatqna-tgi' | awk '{print $1}')
kubectl get pod $POD_NAME -o jsonpath='{.spec.runtimeClassName}'
```

In the output you should see:

```text
kata-qemu-tdx
```

This is a simple indicator that the pod is running in a Trust Domain protected by Intel TDX.
However, for a production use-case, the attestation process is crucial to verify the integrity of the pod.
You may read more about how to enable attestation [here](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/03/demo_workload_deployment/#pod-isolated-by-kata-containers-protected-with-intel-tdx-and-quote-verified-using-intel-trust-authority).


### Customization of deployment configuration

If you want to have more control over what is protected with Intel TDX or use a different deployment file, you can manually modify the deployment configuration, by following the steps below: 

1. Run the script to modify the chosen services with the changes described in [previous section](#overview-of-the-changes-needed):

   ```bash
   SERVICES=("llm-uservice")
   FILE=chatqna.yaml
   for SERVICE in "${SERVICES[@]}"; do
      yq eval '
      (select(.kind == "Deployment" and .metadata.name == "'"$SERVICE"'") | .spec.template.metadata.annotations."io.katacontainers.config.runtime.create_container_timeout") = "800"
      ' "$FILE" -i;
      yq eval '
      (select(.kind == "Deployment" and .metadata.name == "'"$SERVICE"'") | .spec.template.spec.runtimeClassName) = "kata-qemu-tdx"
      ' "$FILE" -i;
   done
   ```

2. For each service, define the resources that must be assigned to the pod to run the service efficiently.
   The resources must be defined in the `resources` section of the pod's container definition.
   The `memory` must be at least 2x the image size.
   The `cpu` and `memory` resources must be defined at least in `limits` sections.
   By default, the pod will be assigned 1 CPU and 2048 MiB of memory, but half of it will be used for filesystem.

3. Apply the changes to the deployment configuration:

   ```bash
   kubectl apply -f chatqna.yaml
   ```

### Troubleshoting

In case of any problems regarding pod creation, refer to [Troubleshooting guide](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/04/troubleshooting/).
