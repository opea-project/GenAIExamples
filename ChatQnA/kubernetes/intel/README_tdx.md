# Deploy ChatQnA in Kubernetes Cluster on Xeon with Intel TDX

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline components on Intel Xeon server where the microservices are protected by [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html).
The guide references the project [GenAIInfra](https://github.com/opea-project/GenAIInfra.git) to prepare the infrastructure. 

The deployment process is intended for users who want to deploy ChatQnA services:

- with pods protected by Intel TDX,
- on a single node in a cluster (acting as a master and worker) that is a Xeon 5th Gen platform or later,
- running Ubuntu 24.04,
- using images pushed to public repository, like quay.io or docker hub.

It's split into 3 sections:

1. [Cluster Configuration](#cluster-configuration) - steps required to prepare components in the cluster required to use Intel TDX.
2. [Node configuration](#node-configuration) - additional steps to be performed on the node that are required to run heavy applications like OPEA ChatQnA.
3. [ChatQnA Services Configuration and Deployment](#chatqna-services-configuration-and-deployment) - describes how to deploy ChatQnA services with Intel TDX protection.

> [!NOTE]
> Running TDX-protected services requires the user to define the pod's resources request (cpu, memory).
>
> Due to lack of hotplugging feature in TDX, the assigned resources cannot be changed after the pod is scheduled and the resources will not be shared with any other pod.
>
> This means, that the total amount of resources assigned to all TDX-protected pods must be less than the total amount of resources available on the node, leaving room for the non-TDX pods requests.


## Cluster Configuration

To prepare cluster to run Intel TDX-protected workloads, follow [Intel Confidential Computing Documentation](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/01/introduction/index.html).


## Node Configuration


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


## ChatQnA Services Configuration and Deployment

To protect a single component with Intel TDX, user must modify its manifest file.
The process is described in details in the [Demo Workload Deployment](https://cc-enabling.trustedservices.intel.com/intel-confidential-containers-guide/03/demo_workload_deployment/#pod-isolated-by-kata-containers-protected-with-intel-tdx-and-quote-verified-using-intel-trust-authority).

As an example we will use the `llm-uservice` component from the ChatQnA pipeline and deploy it using helm charts.

Steps:

1. Export the address of KBS deployed in previous steps.
   If the KBS was deployed in your cluster, you can get the address by running the following command:

    ```bash
    export KBS_ADDRESS=http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}'):$(kubectl get svc kbs -n coco-tenant -o jsonpath='{.spec.ports[0].nodePort}'); \
    echo $KBS_ADDRESS
    ```
   
2. Find the manifest for `llm-uservice` component (e.g.: GenAIInfra/microservices-connector/config/manifests/llm-uservice.yaml).
3. Add the following annotations to the manifest file and replace KBS_ADDRESS with actual value:

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
           io.katacontainers.config.hypervisor.kernel_params: "agent.guest_components_rest_api=all agent.aa_kbc_params=cc_kbc::<KBS_ADDRESS>" # <<--- enable attestation through KBS and provide the KBS address to the pod
           io.katacontainers.config.runtime.create_container_timeout: "600" # <<--- increase the timeout for container creation
       spec:
         runtimeClassName: kata-qemu-tdx # <<--- this is required to start the pod in Trust Domain (TD, virtual machine protected with Intel TDX)
         initContainers: # <<--- this is required to perform attestation before the main container starts
           - name: init-attestation
             image: storytel/alpine-bash-curl:latest
             command: ["/bin/sh","-c"]
             args:
               - |
                 echo starting;
                 (curl http://127.0.0.1:8006/aa/token\?token_type\=kbs | grep -iv "get token failed" | grep -iv "error" | grep -i token && echo "ATTESTATION COMPLETED SUCCESSFULLY") || (echo "ATTESTATION FAILED" && exit 1); 
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

   Note, that due to the nature of TDX, the resources assigned to the pod cannot be shared with any other pod.

4. Deploy the GMC as usual using helm:

    ```bash
    helm install -n system --create-namespace gmc .
    ```
   
5. After the `gmc-controller` pod is running, deploy the chatqna:

   ```bash
   kubectl create ns chatqa; \
   kubectl apply -f cpu/xeon/gmc/chatQnA_xeon.yaml
   ```
   
6. After the services are up, you may verify that the `llm-uservice` is running in a Trust Domain by checking the pod's status:

    ```bash
    # Find the pod name
    POD_NAME=$(kubectl get pods -n chatqa | grep 'llm-svc-deployment-' | awk '{print $1}')
    # Print the runtimeClassName
    kubectl get pod $POD_NAME -n chatqa -o jsonpath='{.spec.runtimeClassName}'
    echo ""
    # Find the initContainer name
    INIT_CONTAINER_NAME=$(kubectl get pod $POD_NAME -n chatqa -o jsonpath='{.spec.initContainers[0].name}')
    # Print the logs of the initContainer
    kubectl logs $POD_NAME -n chatqa -c $INIT_CONTAINER_NAME | grep -i attestation
    ```
   
   The output should contain the `kata-qemu-tdx` runtimeClassName and the `ATTESTATION COMPLETED SUCCESSFULLY` message.
   
   ```text
   kata-qemu-tdx
   ATTESTATION COMPLETED SUCCESSFULLY
   ```

At this point you have successfully deployed the ChatQnA services with the `llm-uservice` component running in a Trust Domain protected by Intel TDX. 
