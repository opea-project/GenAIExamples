# Deploy example application in Kubernetes Cluster on Xeon with Intel TDX

This document outlines the deployment process for an example application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline components on Intel Xeon server where the microservices are protected by [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html).

The deployment process is intended for users who want to deploy an example application:

- with pods protected by Intel TDX,
- on a single node in a cluster (acting as a master and worker) that is a Xeon 4th Gen platform or later,
- running Ubuntu 24.04,
- using images pushed to public repository, like quay.io or docker hub.


## Getting Started

Follow the below steps on the Xeon server node to deploy the example application:

1. [Install Ubuntu 24.04 and enable Intel TDX](https://github.com/canonical/tdx/blob/noble-24.04/README.md#setup-host-os)
2. [Install Kubernetes cluster](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/) 
3. [Install Confidential Containers Operator](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/02/infrastructure_setup/#install-confidential-containers-operator)
4. Increase the kubelet timeout:

   ```bash
   sudo sed -i 's/runtimeRequestTimeout: .*/runtimeRequestTimeout: 30m/' "/var/lib/kubelet/config.yaml"
   sudo systemctl daemon-reload && sudo systemctl restart kubelet
   ```
   
5. Deploy ChatQnA:

   ```bash
   kubectl apply -f cpu/xeon/manifest/chatqna_tdx.yaml
   ```
   
6. Verify all pods are running:

   ```bash
   kubectl get pods
   ```


## Advanced configuration

To protect a single component with Intel TDX, user must modify its manifest file.
The details are described in the [Demo Workload Deployment](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/03/demo_workload_deployment/#pod-isolated-by-kata-containers-and-protected-by-intel-tdx).

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


### Customization of deployment configuration

If you want to have more control over what is protected with Intel TDX or use a different deployment file, you can manually modify the deployment configuration, by following the steps below: 

1. Run the script to apply changes only to the chosen `SERVICES` on the `FILE` of your choice:

   ```bash
   SERVICES=("llm-uservice")
   FILE=cpu/xeon/manifest/chatqna.yaml
   for SERVICE in "${SERVICES[@]}"; do
      yq eval '
      (select(.kind == "Deployment" and .metadata.name == "'"$SERVICE"'") | .spec.template.metadata.annotations."io.katacontainers.config.runtime.create_container_timeout") = "800"
      ' "$FILE" -i;
      yq eval '
      (select(.kind == "Deployment" and .metadata.name == "'"$SERVICE"'") | .spec.template.spec.runtimeClassName) = "kata-qemu-tdx"
      ' "$FILE" -i;
   done
   ```

2. For each service from `SERVICES`, edit the deployment `FILE` to define the resources that must be assigned to the pod to run the service efficiently:
   
   - The resources must be defined in the `resources` section of the pod's container definition.
   - The `memory` must be at least 2x the image size.
   - By default, the pod will be assigned 1 CPU and 2048 MiB of memory, but half of it will be used for filesystem.

3. Apply the changes to the deployment configuration:

   ```bash
   kubectl apply -f chatqna.yaml
   ```

> [!IMPORTANT]
> Total amount of resources assigned to all TDX-protected pods must be less than the total amount of resources available on the node, leaving room for the non-TDX pods requests.


## Troubleshoting

In case of any problems regarding pod creation, refer to [Troubleshooting guide](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/04/troubleshooting/).
