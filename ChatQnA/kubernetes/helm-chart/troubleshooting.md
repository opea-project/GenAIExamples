# ChatQnA Troubleshooting

After deploying chatqna with helm chart, we can use the following command to check whether each service is working properly.
These commands show the steps how RAG work with LLM.

## a function to get the endpoint of service

This is a based command to get each service endpoint of chatqna components.

```bash
svc_endpoint() {
  endpoint=$(kubectl -n ${2:-default} get svc -l ${1} -o jsonpath='{.items[0].spec.clusterIP}:{.items[0].spec.ports[0].port}')
  echo "${endpoint}"
}
```

## define the namespace of service

Please specify the namespace of chatqna, it will be **default** if not define.

```
# define your namespace
ns=opea-chatqna
```

Check the available namespace by:

```console
kubectl get ns
NAME                          STATUS   AGE
calico-system                 Active   21d
cert-manager                  Active   21d
default                       Active   21d
kube-public                   Active   21d
kube-system                   Active   21d
nfd                           Active   21d
observability                 Active   21d
opea-chatqna                  Active   21d
openebs                       Active   21d
orchestrator-system           Active   21d
tigera-operator               Active   21d
```

## Update a file to database

This step will upload a pdf about nike revenue information to vector database.

```bash
# data-prep
label='app.kubernetes.io/name=data-prep'

wget https://raw.githubusercontent.com/opea-project/GenAIComps/refs/heads/main/comps/retrievers/redis/data/nke-10k-2023.pdf

endpoint=$(svc_endpoint ${label} ${ns})
echo $endpoint
curl -x "" -X POST "http://${endpoint}/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./nke-10k-2023.pdf"
```

> **_NOTE:_** Get the service label by:
>
> ```bash
> kubectl get -n ${ns} svc -o json | jq .items[].metadata.labels
> ```
>
> you can use **grep** to filter the labels by key.

## get the embedding of input

This step will get the embedding of your input/question.

```bash
label='app.kubernetes.io/name=tei'
input="What is the revenue of Nike in 2023?"

endpoint=$(svc_endpoint ${label} ${ns})
echo $endpoint

your_embedding=$(curl -x "" http://${endpoint}/embed \
    -X POST \
    -d '{"inputs":"'"$input"'"}' \
    -H 'Content-Type: application/json' |jq .[0] -c)
```

## get the retriever docs

This step will get related docs related to your input/question.

```bash
label='app.kubernetes.io/name=retriever-usvc'
text=$input

endpoint=$(svc_endpoint ${label} ${ns})
echo $endpoint

retrieved_docs=$(curl -x "" http://${endpoint}/v1/retrieval \
  -X POST \
  -d "{\"text\":\"${text}\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json' | jq -c .retrieved_docs)
```

## reranking the docs

This step will get related docs most relevant to your input/question.

```bash
label='app.kubernetes.io/name=reranking-usvc'
query=$input

endpoint=$(svc_endpoint ${label} ${ns})
echo $endpoint

reranking_docs=$(curl -x "" http://${endpoint}/v1/reranking \
  -X POST \
  -d '{"initial_query":"'"$query"'", "retrieved_docs": '"$retrieved_docs"'}' \
  -H 'Content-Type: application/json' | jq -c .documents[0])

# remove "
reranking_docs=$(sed 's/\\"/ /g' <<< "${reranking_docs}")
reranking_docs=$(tr -d '"' <<< "${reranking_docs}")
```

## TGI Q and A

This step will render the answer of your question.

```bash
label='app.kubernetes.io/name=tgi'

endpoint=$(svc_endpoint ${label} ${ns})
echo $endpoint

# your question
query=${input}
# inputs template.
inputs="### You are a helpful, respectful and honest assistant to help the user with questions. Please refer to the search results obtained from the local knowledge base. But be careful to not incorporate the information that you think is not relevant to the question. If you don't know the answer to a question, please don't share false information. ### Search results: ${reranking_docs} ### Question: ${query} \n\n### Answer:"

curl -x "" http://${endpoint}/generate \
  -X POST \
  -d '{"inputs":"'"${inputs}"'","parameters":{"max_new_tokens":1024, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

The output

```console
{"generated_text":" In fiscal 2023, NIKE, Inc. achieved record Revenues of $51.2 billion."}
```

## REF

[Build Mega Service of ChatQnA on Xeon](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/docker_compose/intel/cpu/xeon/README.md)
