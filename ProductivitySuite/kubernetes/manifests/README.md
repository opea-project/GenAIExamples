# Deploy ProductivitySuite with ReactUI

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

## Prerequisites for Deploying ProductivitySuite with ReactUI:
To begin with, ensure that you have following prerequisites in place:

1. Kubernetes installation: Make sure that you have Kubernetes installed.
2. Images: Make sure you have all the images ready for the examples and components stated above. You may refer to [README](../../docker/xeon/README.md) for steps to build the images.
3. Configuration Values: Set the following values in all the yaml files before proceeding with the deployment:

   a. HUGGINGFACEHUB_API_TOKEN (Your HuggingFace token to download your desired model from HuggingFace):
      ```
      # You may set the HUGGINGFACEHUB_API_TOKEN via method:
      export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
      cd GenAIExamples/ProductivitySuite/kubernetes/manifests/xeon/
      sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" *.yaml
      ```

   b. Set the proxies based on your network configuration
      ```
      # Look for http_proxy, https_proxy and no_proxy key and fill up the values for all the yaml files with your system proxy configuration.
      ```

   c. Set all the backend service endpoint for REACT UI service
      ```
      # Setup all the backend service endpoint in productivity_suite_reactui.yaml for UI to consume with.
      # Look for ENDPOINT in the yaml and insert all the url endpoint for all the required backend service.
      ```

4. MODEL_ID and model-volume (OPTIONAL): You may as well customize the "MODEL_ID" to use different model and model-volume for the volume to be mounted.
5. After finish with steps above, you can proceed with the deployment of the yaml file.

## Deploying ProductivitySuite
You can use yaml files in xeon folder to deploy ProductivitySuite with reactUI.
```
cd GenAIExamples/ProductivitySuite/kubernetes/manifests/xeon/
kubectl apply -f *.yaml
```

## User Management via Keycloak Configuration
Please refer to [keycloak_setup_guide](../../docker/xeon/keycloak_setup_guide.md) for more detail related to Keycloak configuration setup.

## Verify Services
To verify the installation, run command 'kubectl get pod' to make sure all pods are running.

To view all the available services, run command 'kubectl get svc' to obtain ports that need to used as backend service endpoint in productivity_suite_reactui.yaml.

You may use `kubectl port-forward service/<service_name> <forwarded_port>/<service_port>` to forward the port of all the services if necessary.
```
# For example, 'kubectl get svc | grep productivity'
productivity-suite-react-ui   ClusterIP      10.96.3.236     <none>        80/TCP

# By default, productivity-suite-react-ui service export port 80, forward it to 5174 via command:
'kubectl port-forward service/productivity-suite-react-ui 5174:80'
```

You may open up the productivity suite react UI by using http://localhost:5174 in the browser.
