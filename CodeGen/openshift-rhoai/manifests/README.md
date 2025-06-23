<h1 align="center" id="title">Deploy CodeGen on OpenShift Cluster with RHOAI</h1>

## Prerequisites

1. **Red Hat OpenShift Cluster** with dynamic _StorageClass_ to provision _PersistentVolumes_ e.g. **OpenShift Data Foundation**) and installed Operators: **Red Hat - Authorino (Technical Preview)**, **Red Hat OpenShift Service Mesh**, **Red Hat OpenShift Serverless** and **Red Hat Openshift AI**.
2. Exposed image registry to push there docker images (https://docs.openshift.com/container-platform/4.16/registry/securing-exposing-registry.html).
3. Access to S3-compatible object storage bucket (e.g. **OpenShift Data Foundation**, **AWS S3**) and values of access and secret access keys and S3 endpoint (https://docs.redhat.com/en/documentation/red_hat_openshift_data_foundation/4.16/html/managing_hybrid_and_multicloud_resources/accessing-the-multicloud-object-gateway-with-your-applications_rhodf#accessing-the-multicloud-object-gateway-with-your-applications_rhodf)\
4. Account on https://huggingface.co/, access to model _ise-uiuc/Magicoder-S-DS-6.7B_ (for Xeon) or _meta-llama/CodeLlama-7b-hf_ (for Gaudi) and token with _Read permissions_. Update the access token in your repository using following commands.

On Xeon:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/xeon
export HFTOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HFTOKEN}/g" codegen.yaml servingruntime-magicoder.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/gaudi
export HFTOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HFTOKEN}/g" codegen.yaml servingruntime-codellama.yaml
```

## Deploy model in Red Hat Openshift AI

1. Log in to OpenShift CLI and run following commands to create new serving runtime.

On Xeon:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/xeon
oc apply -f servingruntime-magicoder.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/gaudi
oc apply -f servingruntime-codellama.yaml
```

Verify if template has been created with `oc get template -n redhat-ods-applications` command.

2. Find the route for **Red Hat OpenShift AI** dashboard with below command and open it in the browser:

```
oc get routes -A | grep rhods-dashboard
```

3. Go to **Data Science Project** and click **Create data science project**. Fill the **Name** and click **Create**.
4. Go to **Workbenches** tab and click **Create workbench**. Fill the **Name**, under **Notebook image** choose _Standard Data Science_, under **Cluster storage** choose _Create new persistent storage_ and change **Persistent storage size** to 40 GB. Click **Create workbench**.
5. Open newly created Jupiter notebook and run following commands to download the model and upload it on s3:

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

For Xeon download _ise-uiuc/Magicoder-S-DS-6.7B_:

```
snapshot_download("ise-uiuc/Magicoder-S-DS-6.7B", cache_dir=f'./models', token=hf_token)
```

For Gaudi download _meta-llama/CodeLlama-7b-hf_:

```
snapshot_download("meta-llama/CodeLlama-7b-hf", cache_dir=f'./models', token=hf_token)
```

Upload the downloaded model to S3:

```
files = (file for file in glob.glob(f'{path}/**/*', recursive=True) if os.path.isfile(file) and "snapshots" in file)
for filename in files:
    s3_name = filename.replace(path, '')
    print(f'Uploading: {filename} to {path}{s3_name}')
    bucket.upload_file(filename, f'{path}{s3_name}')
```

6. Go to your project in **Red Hat OpenShift AI** dashboard, then "Models" tab and click **Deploy model** under _Single-model serving platform_. Fill the **Name**, choose newly created **Serving runtime**: _Text Generation Inference Magicoder-S-DS-6.7B on CPU_ (for Xeon) or _Text Generation Inference CodeLlama-7b-hf on Gaudi_ (for Gaudi), **Model framework**: _llm_ and change **Model server size** to _Custom_: 16 CPUs and 64 Gi memory. For deployment with Gaudi select proper **Accelerator**. Click the checkbox to create external route in **Model route** section and uncheck the token authentication. Under **Model location** choose _New data connection_ and fill all required fields for s3 access, **Bucket** _first.bucket_ and **Path**: _models_. Click **Deploy**. It takes about 10 minutes to get _Loaded_ status.\
   If it's not going to _Loaded_ status and revision changed status to "ProgressDeadlineExceeded" (`oc get revision`), scale model deployment to 0 and than to 1 with command `oc scale deployment.apps/<model_deployment_name> --replicas=1` and wait about 10 minutes for deployment.

## Deploy CodeGen

1. Login to OpenShift CLI, go to your project and find the URL of TGI_LLM_ENDPOINT:

```
oc get service.serving.knative.dev
```

Update the TGI_LLM_ENDPOINT in your repository.

On Xeon:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/xeon
export TGI_LLM_ENDPOINT="YourURL"
sed -i "s#insert-your-tgi-url-here#${TGI_LLM_ENDPOINT}#g" codegen.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/gaudi
export TGI_LLM_ENDPOINT="YourURL"
sed -i "s#insert-your-tgi-url-here#${TGI_LLM_ENDPOINT}#g" codegen.yaml
```

2. Build docker images locally

- LLM Docker Image:

```
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

- MegaService Docker Image:

```
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen
docker build -t opea/codegen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

- UI Docker Image:

```
cd GenAIExamples/CodeGen/ui
docker build -t opea/codegen-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

To verify run the command: `docker images`.

3. Login to docker, tag the images and push it to image registry with following commands:

```
docker login -u <user> -p $(oc whoami -t) <openshift-image-registry_route>
docker tag <image_id> <openshift-image-registry_route>/<namespace>/<image_name>:<tag>
docker push <openshift-image-registry_route>/<namespace>/<image_name>:<tag>
```

To verify run the command: `oc get istag`.

4. Use the _IMAGE REFERENCE_ from previous step to update images names in manifest files.

On Xeon:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/xeon
export IMAGE_LLM_TGI="YourImage"
export IMAGE_CODEGEN="YourImage"
export IMAGE_CODEGEN_UI="YourImage"
sed -i "s#insert-your-image-llm-tgi#${IMAGE_LLM_TGI}#g" codegen.yaml
sed -i "s#insert-your-image-codegen#${IMAGE_CODEGEN}#g" codegen.yaml
sed -i "s#insert-your-image-codegen-ui#${IMAGE_CODEGEN_UI}#g" ui-server.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/gaudi
export IMAGE_LLM_TGI="YourImage"
export IMAGE_CODEGEN="YourImage"
export IMAGE_CODEGEN_UI="YourImage"
sed -i "s#insert-your-image-llm-tgi#${IMAGE_LLM_TGI}#g" codegen.yaml
sed -i "s#insert-your-image-codegen#${IMAGE_CODEGEN}#g" codegen.yaml
sed -i "s#insert-your-image-codegen-ui#${IMAGE_CODEGEN_UI}#g" ui-server.yaml
```

5. Create _rhoai-ca-bundle_ secret:

```
oc create secret generic rhoai-ca-bundle --from-literal=tls.crt="$(oc extract secret/knative-serving-cert -n istio-system --to=- --keys=tls.crt)"
```

6. Deploy CodeGen with command:

```
oc apply -f codegen.yaml
```

7. Check the _codegen_ route with command `oc get routes` and update the route in _ui-server.yaml_ file:

On Xeon:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/xeon
export CODEGEN_ROUTE="YourCodegenRoute"
sed -i "s/insert-your-codegen-route/${CODEGEN_ROUTE}/g" ui-server.yaml
```

On Gaudi:

```
cd GenAIExamples/CodeGen/openshift-rhoai/manifests/gaudi
export CODEGEN_ROUTE="YourCodegenRoute"
sed -i "s/insert-your-codegen-route/${CODEGEN_ROUTE}/g" ui-server.yaml
```

8. Deploy UI with command:

```
oc apply -f ui-server.yaml
```

## Verify Services

Make sure all the pods are running, and restart the codegen-xxxx pod if necessary.

```
oc get pods
curl http://${CODEGEN_ROUTE}/v1/codegen -H "Content-Type: application/json" -d '{
     "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
     }'
```

## Launch the UI

To access the frontend, find the route for _ui-server_ with command `oc get routes` and open it in the browser.
