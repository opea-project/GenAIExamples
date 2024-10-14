# 🚀 Deploy ProductivitySuite with ReactUI

The document outlines the deployment steps for ProductivitySuite via Kubernetes cluster while utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline components and ReactUI, a popular React-based user interface library.

In ProductivitySuite, it consists of following pipelines/examples and components:
```
- productivity-suite-react-ui
- chatqna
- codegen
- docsum
- faqgen
- dataprep via redis
- chat-history
- prompt-registry
- mongo
- keycloak
```

---

## ⚠️ Prerequisites for Deploying ProductivitySuite with ReactUI
To begin with, ensure that you have following prerequisites in place:

1. ☸ Kubernetes installation: Make sure that you have Kubernetes installed.
2. 🐳 Images: Make sure you have all the images ready for the examples and components stated above. You may refer to [README](../../docker_compose/intel/cpu/xeon/README.md) for steps to build the images.
3. 🔧 Configuration Values: Set the following values in all the yaml files before proceeding with the deployment:

   Download and set up yq for YAML processing:
   ```
   sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
   sudo chmod a+x /usr/local/bin/yq

   cd GenAIExamples/ProductivitySuite/kubernetes/intel/cpu/xeon/manifest/
   . ../utils
   ```

   a. HUGGINGFACEHUB_API_TOKEN (Your HuggingFace token to download your desired model from HuggingFace):
      ```
      # You may set the HUGGINGFACEHUB_API_TOKEN via method:
      export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
      set_hf_token $HUGGINGFACEHUB_API_TOKEN
      ```

   b. Set the proxies based on your network configuration
      ```
      # Look for http_proxy, https_proxy and no_proxy key and fill up the values for all the yaml files with your system proxy configuration.
      set_http_proxy $http_proxy
      set_https_proxy $https_proxy
      set_no_proxy $no_proxy
      ```

   c. Set all the backend service endpoint for REACT UI service
      ```
      # Setup all the backend service endpoint in productivity_suite_reactui.yaml for UI to consume with.
      # Look for ENDPOINT in the yaml and insert all the url endpoint for all the required backend service.
      set_services_endpoint
      ```

4. MODEL_ID and model-volume **(OPTIONAL)**: You may as well customize the "MODEL_ID" to use different model and model-volume for the volume to be mounted.
      ```
      sudo mkdir -p /mnt/opea-models
      sudo chmod -R a+xwr /mnt/opea-models
      set_model_id
      ```
5. MODEL_MIRROR **(OPTIONAL)**: Please set the exact huggingface mirror if cannot access huggingface website directly from your country. You can set it as https://hf-mirror.com in PRC.
      ```
      set_model_mirror
      ```
6. After finish with steps above, you can proceed with the deployment of the yaml file.
      ```
      git diff
      ```

---

##  🌐 Deploying ProductivitySuite
You can use yaml files in xeon folder to deploy ProductivitySuite with reactUI.
```
cd GenAIExamples/ProductivitySuite/kubernetes/intel/cpu/xeon/manifests/
kubectl apply -f .
```

---

## 🔐 User Management via Keycloak Configuration
Please refer to **[keycloak_setup_guide](../../docker_compose/intel/cpu/xeon/keycloak_setup_guide.md)** for more detail related to Keycloak configuration setup.

---

## ✅ Verify Services
To verify the installation, run command 'kubectl get pod' to make sure all pods are running.

To view all the available services, run command 'kubectl get svc' to obtain ports that need to used as backend service endpoint in productivity_suite_reactui.yaml.

You may use `kubectl port-forward service/<service_name> <forwarded_port>/<service_port>` to forward the port of all the services if necessary.
```
# For example, 'kubectl get svc | grep productivity'
productivity-suite-react-ui   ClusterIP      10.96.3.236     <none>        80/TCP

# By default, productivity-suite-react-ui service export port 80, forward it to 5174 via command:
'kubectl port-forward service/productivity-suite-react-ui 5174:80'
```

Or simple way to forward the productivity suite service port.
```
label='app.kubernetes.io/name=react-ui'
port=$(kubectl -n ${ns:-default} get svc -l ${label} -o jsonpath='{.items[0].spec.ports[0].port}')
kubectl port-forward service/productivity-suite-react-ui 5174:$port
```

You may open up the productivity suite react UI by using http://localhost:5174 in the browser.
