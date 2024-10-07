<h1 align="center" id="title">Deploy ChatQnA on OpenShift Cluster</h1>

## Prerequisites

1. **Red Hat OpenShift Cluster** with dynamic *StorageClass* to provision *PersistentVolumes* e.g. **OpenShift Data Foundation**) and installed Operators: **Red Hat - Authorino (Technical Preview)**, **Red Hat OpenShift Service Mesh**, **Red Hat OpenShift Serverless** and **Red Hat Openshift AI**.
2. Exposed image registry to push docker images (https://docs.openshift.com/container-platform/4.16/registry/securing-exposing-registry.html).
3. Access to S3-compatible object storage bucket (e.g. **OpenShift Data Foundation**, **AWS S3**) and values of access and secret access keys and S3 endpoint (https://docs.redhat.com/en/documentation/red_hat_openshift_data_foundation/4.16/html/managing_hybrid_and_multicloud_resources/accessing-the-multicloud-object-gateway-with-your-applications_rhodf#accessing-the-multicloud-object-gateway-with-your-applications_rhodf)
4. (Optional) Create a new OpenShift project for ChatQnA resources:
     ```
     export PROJECT="YourOwnProject"
     oc new-project ${PROJECT}
     ```
5. Access to https://huggingface.co/ to get access token with *Read* permissions. Also, get the LangChain API key.\
    Update the access token and the key in your repository:
    ```
    cd GenAIExamples/ChatQnA/openshift-rhoai/manifests/xeon
    export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
    export LANGCHAIN_API_KEY="YourOwnKey"
    export PROJECT="YourOwnProject"
    sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" chatqna.yaml servingruntime.yaml
    sed -i "s/insert-your-langchain-key-here/${LANGCHAIN_API_KEY}/g" chatqna.yaml servingruntime.yaml
    sed -i "s/insert-your-namespace-here/${PROJECT}/g" chatqna.yaml servingruntime.yaml
    ```

## Deploy model in Red Hat Openshift AI

1. Log in to the Openshift Container Platform web console and select **Operators** > **OperatorHub**.
2. Open **Red Hat OpenShift AI** dashboard: go to **Networking** -> **Routes** and find location for *rhods-dashboard*).
3. Go to **Data Science Project** and click **Create data science project**. Fill in the **Name** and click **Create**.
4. Go to **Workbenches** tab and click **Create workbench**. Fill in the **Name**, under **Notebook image** choose *Standard Data Science*, under **Cluster storage** choose *Create new persistent storage*, and change **Persistent storage size** to 40 GB. Under **Data connections** choose *Create new data connection* and fill in all required fields for s3 access including bucket name. Click **Create workbench**.
5. Open the newly created Jupiter notebook and run the following commands to download the model and upload it on s3:
    ```
    %env S3_ENDPOINT=<S3_RGW_ROUTE>
    %env S3_ACCESS_KEY=<AWS_ACCESS_KEY_ID>
    %env S3_SECRET_KEY=<AWS_SECRET_ACCESS_KEY>
    %env HF_TOKEN=<PASTE_HUGGINGFACE_TOKEN>
    ```
    ```
    !pip install huggingface-hub
    ```
    ```
    import os
    import boto3
    import botocore
    import glob
    from huggingface_hub import snapshot_download
    bucket_name = 'first.bucket'
    s3_endpoint = os.environ.get('S3_ENDPOINT')
    s3_accesskey = os.environ.get('S3_ACCESS_KEY')
    s3_secretkey = os.environ.get('S3_SECRET_KEY')
    path = 'models'
    hf_token = os.environ.get('HF_TOKEN')
    session = boto3.session.Session()
    s3_resource = session.resource('s3',
                                endpoint_url=s3_endpoint,
                                verify=False,
                                aws_access_key_id=s3_accesskey,
                                aws_secret_access_key=s3_secretkey)
    bucket = s3_resource.Bucket(bucket_name)
    ```
    ```
    snapshot_download("ise-uiuc/Magicoder-S-DS-6.7B", cache_dir=f'./models', token=hf_token, revision="refs/pr/11")
    ```
    ```
    files = (file for file in glob.glob(f'{path}/**/*', recursive=True) if os.path.isfile(file) and "snapshots" in file)
    for filename in files:
        s3_name = filename.replace(path, '')
        print(f'Uploading: {filename} to {path}{s3_name}')
        bucket.upload_file(filename, f'{path}{s3_name}')
    ```
6. Back to **Red Hat OpenShift AI** dashboard, go to **Settings** -> **Serving runtimes** and click **Add serving runtime**. Choose *Single-model serving platform* and *REST* as API protocol. Upload the file or copy the content of *servingruntime.yaml*.

7. Go to your project, then the "Models" tab, and click **Deploy model** under *Single-model serving platform*. Fill in the **Name**, choose newly created **Serving runtime**: *Text Generation Inference 2.2.0 Intel/neural-chat-7b-v3-3 on CPU*, **Model framework**: *neural-chat* and change **Model server size** to *Custom*: 16 CPUs and 64 Gi memory. Under **Model location** choose *Existing data connection* and **Path**: *models*. Click **Deploy**. It takes about 30 minutes to get *Loaded* status.
    If it's not going to *Loaded* status and revision changed status to "ProgressDeadlineExceeded" (``oc get revision``), then apply the below commands which increase timeout and scale model deployment to 0 and then to 1:
    ```
    oc patch --type=merge -n knative-serving knativeserving knative-serving --patch '{"spec":{"config":{"deployment":{"progress-deadline":"30m"}}}}'
    oc -n <DATA_SCIENCE_PROJECT_NAME> scale deployment.apps -l component=predictor --replicas=1
    ```
    Replace `<DATA_SCIENCE_PROJECT_NAME>` with the project name created in the "3" item list of this document section. In this case, the project name is also used as a namespace name for deployed components. Please keep in mind that this is a different namespace name as it is in the prerequisites section of this document.
    Wait about 30 minutes for deployment.

## Deploy ChatQnA On Xeon
1. Log in to OpenShift CLI, go to your project, and find the URL of TGI_LLM_ENDPOINT:
    ```
    oc -n <DATA_SCIENCE_PROJECT_NAME> get service.serving.knative.dev -o jsonpath='{.items[0].status.url}'
    ```
    Update the TGI_LLM_ENDPOINT in your repository:
    ```
    cd GenAIExamples/ChatQnA/openshift-rhoai/manifests/xeon
    export TGI_LLM_ENDPOINT="YourURL"
    sed -i "s#insert-your-tgi-url-here#${TGI_LLM_ENDPOINT}#g" chatqna.yaml
    ```

2. Build docker images locally
    ```bash
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps
    ```

- Build Embedding Image

    ```bash
    docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
    ```

- Build Retriever Image

    ```bash
    docker build --no-cache -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./comps/retrievers/langchain/redis/docker/Dockerfile .
    ```

- Build Rerank Image

    ```bash
    docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./comps/reranks/langchain-mosec/docker/Dockerfile .
    ```

- Build LLM Image

    Use TGI as the backend:

    ```bash
    docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
    ```

- Build Dataprep Image

    ```bash
    docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
    cd ..
    ```

- Build MegaService Docker Image

    To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via the below command:

    ```bash
    git clone https://github.com/opea-project/GenAIExamples.git
    cd GenAIExamples/ChatQnA/docker
    docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    cd ../../..
    ```

    To verify run `docker images` command and you should have the following container images:

    - `opea/chatqna:latest`
    - `opea/dataprep-redis:latest`
    - `opea/embedding-tei:latest`
    - `opea/llm-tgi:latest`
    - `opea/reranking-tei:latest`
    - `opea/retriever-redis:latest`

3. Log in to Podman, tag the images, and push them to the image registry with the following commands:

    ```
    podman login -u <user> -p $(oc whoami -t) <openshift-image-registry_route> --tls-verify=false
    podman tag <image_id> <openshift-image-registry_route>/<namespace>/<image_name>:<tag>
    podman push <openshift-image-registry_route>/<namespace>/<image_name>:<tag>
    ```
    To verify run the command: `oc get istag`.

4. Create *rhoai-ca-bundle* secret:
    ```
    oc create secret generic rhoai-ca-bundle --from-literal=tls.crt="$(oc extract secret/knative-serving-cert -n istio-system --to=- --keys=tls.crt)"
    ```

5. Deploy ChatQnA with command:
    ```
    oc apply -f chatqna.yaml
    ```

## Verify Services

Ensure all the pods are running, and restart the chatqna-xxxx pod if necessary.

Check ChatQnA route:
```
oc get route
```
Use `HOST/PORT` field from the output to populate `YourChatqnaRoute` below and execute the command:
```
oc get pods
export CHATQNA_ROUTE="YourChatqnaRoute"
curl http://${CHATQNA_ROUTE}/v1/chatqna -H "Content-Type: application/json" -d '{
     "messages": "What is the best place for hiking?"
     }'
```
