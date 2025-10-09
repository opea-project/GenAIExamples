# Example HybridRAG deployments on an Intel® Gaudi® Platform

This example covers the single-node on-premises deployment of the HybridRAG example using OPEA components. There are various ways to enable HybridRAG, but this example will focus on four options available for deploying the HybridRAG pipeline to Intel® Gaudi® AI Accelerators.

**Note** This example requires access to a properly installed Intel® Gaudi® platform with a functional Docker service configured to use the habanalabs-container-runtime. Please consult the [Intel® Gaudi® software Installation Guide](https://docs.habana.ai/en/v1.20.0/Installation_Guide/Driver_Installation.html) for more information.

## HybridRAG Quick Start Deployment

This section describes how to quickly deploy and test the HybridRAG service manually on an Intel® Gaudi® platform. The basic steps are:

### Access the Code

Clone the GenAIExample repository and access the HybridRAG Intel® Gaudi® platform Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/HybridRAG/docker_compose/intel/hpu/gaudi/
```

Checkout a released version, such as v1.4:

```
git checkout v1.4
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

To set up environment variables for deploying HybridRAG services, source the _setup_env.sh_ script in this directory:

```
source ./set_env.sh
```

### Deploy the Services Using Docker Compose

To deploy the HybridRAG services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The HybridRAG docker images should automatically be downloaded from the `OPEA registry` and deployed on the Intel® Gaudi® Platform:

```
[+] Running 9/9
 ✔ Container redis-vector-db                      Healthy                                                                           6.4s
 ✔ Container vllm-service                         Started                                                                           0.4s
 ✔ Container tei-embedding-server                 Started                                                                           0.9s
 ✔ Container neo4j-apoc                           Healthy                                                                          11.4s
 ✔ Container tei-reranking-server                 Started                                                                           0.8s
 ✔ Container retriever-redis-server               Started                                                                           1.0s
 ✔ Container dataprep-redis-server                Started                                                                           6.5s
 ✔ Container text2query-cypher-gaudi-container    Started                                                                          12.2s
 ✔ Container hybridrag-xeon-backend-server        Started                                                                          12.4s
```

To rebuild the docker image for the hybridrag-xeon-backend-server container:

```
cd GenAIExamples/HybridRAG
docker build --no-cache -t opea/hybridrag:latest -f Dockerfile .
```

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 10 containers should have started:

```
CONTAINER ID   IMAGE                                                                                       COMMAND                  CREATED        STATUS                  PORTS                                                                                            NAMES
a9286abd0015   opea/hybridrag:latest                                                                       "python hybridrag.py"    15 hours ago   Up 15 hours             0.0.0.0:8888->8888/tcp, :::8888->8888/tcp                                                        hybridrag-xeon-backend-server
8477b154dc72   opea/text2query-cypher:latest                                                               "/bin/sh -c 'bash ru…"   15 hours ago   Up 15 hours             0.0.0.0:11801->9097/tcp, [::]:11801->9097/tcp                                                    text2query-cypher-gaudi-container
688e01a431fa   opea/dataprep:latest                                                                        "sh -c 'python $( [ …"   15 hours ago   Up 15 hours             0.0.0.0:6007->5000/tcp, [::]:6007->5000/tcp                                                      dataprep-redis-server
54f574fe54bb   opea/retriever:latest                                                                       "python opea_retriev…"   15 hours ago   Up 15 hours             0.0.0.0:7000->7000/tcp, :::7000->7000/tcp                                                        retriever-redis-server
5028eb66617c   ghcr.io/huggingface/text-embeddings-inference:cpu-1.6                                       "text-embeddings-rou…"   15 hours ago   Up 15 hours             0.0.0.0:8808->80/tcp, [::]:8808->80/tcp                                                          tei-reranking-server
a9dbf8a13365   opea/vllm:latest                                                                            "python3 -m vllm.ent…"   15 hours ago   Up 15 hours (healthy)   0.0.0.0:9009->80/tcp, [::]:9009->80/tcp                                                          vllm-service
43f44830f47b   neo4j:latest                                                                                "tini -g -- /startup…"   15 hours ago   Up 15 hours (healthy)   0.0.0.0:7474->7474/tcp, :::7474->7474/tcp, 7473/tcp, 0.0.0.0:7687->7687/tcp, :::7687->7687/tcp   neo4j-apoc
867feabb6f11   redis/redis-stack:7.2.0-v9                                                                  "/entrypoint.sh"         15 hours ago   Up 15 hours (healthy)   0.0.0.0:6379->6379/tcp, :::6379->6379/tcp, 0.0.0.0:8001->8001/tcp, :::8001->8001/tcp             redis-vector-db
23cd7f16453b   ghcr.io/huggingface/text-embeddings-inference:cpu-1.6                                       "text-embeddings-rou…"   15 hours ago   Up 15 hours             0.0.0.0:6006->80/tcp, [::]:6006->80/tcp                                                          tei-embedding-server
```

### Test the Pipeline

Once the HybridRAG services are running, run data ingestion. The following command is ingesting unstructure data:

```bash
cd GenAIExamples/HybridRAG/tests
curl -X POST -H "Content-Type: multipart/form-data" \
    -F "files=@./Diabetes.txt" \
    -F "files=@./Acne_Vulgaris.txt" \
    -F "chunk_size=300" \
    -F "chunk_overlap=20" \
    http://${host_ip}:6007/v1/dataprep/ingest
```

The data files (Diabetes.txt and Acne_Vulgaris.txt) are samples downloaded from Wikipedia, and they are here to facilitate the pipeline tests. Users are encouraged to download their own datasets, and the command above should be updated with the proper file names.

As for the structured data, the application is pre-seeded with structured data and schema by default. To create a knowledge graph with custom data and schema, set the cypher_insert environment variable prior to application deployment.

```bash
export cypher_insert='
 LOAD CSV WITH HEADERS FROM "https://docs.google.com/spreadsheets/d/e/2PACX-1vQCEUxVlMZwwI2sn2T1aulBrRzJYVpsM9no8AEsYOOklCDTljoUIBHItGnqmAez62wwLpbvKMr7YoHI/pub?gid=0&single=true&output=csv" AS rows
 MERGE (d:disease {name:rows.Disease})
 MERGE (dt:diet {name:rows.Diet})
 MERGE (d)-[:HOME_REMEDY]->(dt)

 MERGE (m:medication {name:rows.Medication})
 MERGE (d)-[:TREATMENT]->(m)

 MERGE (s:symptoms {name:rows.Symptom})
 MERGE (d)-[:MANIFESTATION]->(s)

 MERGE (p:precaution {name:rows.Precaution})
 MERGE (d)-[:PREVENTION]->(p)
'
```

If the graph database is already populated, you can skip the knowledge graph generation by setting the refresh_db environment variable:

```bash
export refresh_db='False'
```

Now test the pipeline using the following command:

```bash
curl -s -X POST -d '{"messages": "what are the symptoms for Diabetes?"}' \
    -H 'Content-Type: application/json' \
    "${host_ip}:8888/v1/hybridrag"
```

To collect per request latency for the pipeline, run the following:

```bash
curl -o /dev/null -s -w "Total Time: %{time_total}s\n" \
    -X POST \
    -d '{"messages": "what are the symptoms for Diabetes?"}' \
    -H 'Content-Type: application/json' \
    "${host_ip}:8888/v1/hybridrag"
```

**Note** The value of _host_ip_ was set using the _set_env.sh_ script and can be found in the _.env_ file.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
docker compose -f compose.yaml down
```

All the HybridRAG containers will be stopped and then removed on completion of the "down" command.
