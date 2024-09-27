# Start the Pathway Vector DB Server

Set the environment variables for Pathway, and the embedding model.

> Note: If you are using `TEI_EMBEDDING_ENDPOINT`, make sure embedding service is already running.
> See the instructions under [here](../../retrievers/pathway/langchain/README.md)

```bash
export PATHWAY_HOST=0.0.0.0
export PATHWAY_PORT=8666
# TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"  # uncomment if you want to use the hosted embedding service, example: "http://127.0.0.1:6060"
```

## Configuration

### Setting up the Pathway data sources

Pathway can listen to many sources simultaneously, such as local files, S3 folders, cloud storage, and any data stream. Whenever a new file is added or an existing file is modified, Pathway parses, chunks and indexes the documents in real-time.

See [pathway-io](https://pathway.com/developers/api-docs/pathway-io) for more information.

You can easily connect to the data inside the folder with the Pathway file system connector. The data will automatically be updated by Pathway whenever the content of the folder changes. In this example, we create a single data source that reads the files under the `./data` folder.

You can manage your data sources by configuring the `data_sources` in `vectorstore_pathway.py`.

```python
import pathway as pw

data = pw.io.fs.read(
    "./data",
    format="binary",
    mode="streaming",
    with_metadata=True,
)  # This creates a Pathway connector that tracks
# all the files in the ./data directory

data_sources = [data]
```

### Other configs (parser, splitter and the embedder)

Pathway vectorstore handles the ingestion and processing of the documents.
This allows you to configure the parser, splitter and the embedder.
Whenever a file is added or modified in one of the sources, Pathway will automatically ingest the file.

By default, `ParseUnstructured` parser, `langchain.text_splitter.CharacterTextSplitter` splitter and `BAAI/bge-base-en-v1.5` embedder are used.

For more information, see the relevant Pathway docs:

- [Vector store docs](https://pathway.com/developers/api-docs/pathway-xpacks-llm/vectorstore)
- [parsers docs](https://pathway.com/developers/api-docs/pathway-xpacks-llm/parsers)
- [splitters docs](https://pathway.com/developers/api-docs/pathway-xpacks-llm/splitters)
- [embedders docs](https://pathway.com/developers/api-docs/pathway-xpacks-llm/embedders)

## Building and running

Build the Docker and run the Pathway Vector Store:

```bash
docker build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/vectorstore-pathway:latest -f comps/vectorstores/pathway/Dockerfile .

# with locally loaded model, you may add `EMBED_MODEL` env variable to configure the model.
docker run -e PATHWAY_HOST=${PATHWAY_HOST} -e PATHWAY_PORT=${PATHWAY_PORT} -e http_proxy=$http_proxy -e https_proxy=$https_proxy -v ./data:/app/data -p ${PATHWAY_PORT}:${PATHWAY_PORT} opea/vectorstore-pathway:latest

# with the hosted embedder (network argument is needed for the vector server to reach to the embedding service)
docker run -e PATHWAY_HOST=${PATHWAY_HOST} -e PATHWAY_PORT=${PATHWAY_PORT} -e TEI_EMBEDDING_ENDPOINT=${TEI_EMBEDDING_ENDPOINT} -e http_proxy=$http_proxy -e https_proxy=$https_proxy -v ./data:/app/data -p ${PATHWAY_PORT}:${PATHWAY_PORT} --network="host" opea/vectorstore-pathway:latest
```

## Health check the vector store

Wait until the server finishes indexing the docs, and send the following request to check it.

```bash
curl -X 'POST' \
  "http://$PATHWAY_HOST:$PATHWAY_PORT/v1/statistics" \
  -H 'accept: */*' \
  -H 'Content-Type: application/json'
```

This should respond with something like:

> `{"file_count": 1, "last_indexed": 1724325093, "last_modified": 1724317365}`
