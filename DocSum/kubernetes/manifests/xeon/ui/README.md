# Deploy DocSum with ReactUI

The README provides a step-by-step guide on how to deploy DocSum with ReactUI, a popular React-based user interface library in Kubernetes cluster.

You can use react-docsum.yaml to deploy Docsum with reactUI.
```
kubectl apply -f react-docsum.yaml
```

## Prerequisites for Deploying DocSum with ReactUI:
Before deploying the react-docsum.yaml file, ensure that you have the following prerequisites in place:

1. Kubernetes installation: Make sure that you have Kubernetes installed.
2. Configuration Values: Set the following values in react-docsum.yaml before proceeding with the deployment:
    #### a. HUGGINGFACEHUB_API_TOKEN (Your HuggingFace token to download your desired model from HuggingFace):
    ```
    # You may set the HUGGINGFACEHUB_API_TOKEN via method:
    export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
    cd GenAIExamples/DocSum/kubernetes/manifests/xeon/ui/
    sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" react-docsum.yaml
    ```
    #### b. Set the proxies based on your network configuration
    ```
    # Look for http_proxy, https_proxy, no_proxy key and fill up the value with your proxy configuration.
    ```
3. MODEL_ID and model-volume (OPTIONAL): You may as well customize the "MODEL_ID" to use different model and model-volume for the volume to be mounted.
4. After completing these, you can proceed with the deployment of the react-docsum.yaml file.

## Verify Services:
Make sure all the pods are running, you should see total of 4 pods running:
1. docsum
2. docsum-llm-uservice
3. docsum-react-ui
4. docsum-tgi

You may open up the UI by using the docsum-react-ui endpoint in the browser.