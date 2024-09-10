# LanceDB

LanceDB is an embedded vector database for AI applications. It is open source and distributed with an Apache-2.0 license.

LanceDB datasets are persisted to disk and can be shared in Python.

## Setup

```bash
npm install -S vectordb
```

## Usage

### Create a new index from texts

```python
import os
import tempfile
from langchain.vectorstores import LanceDB
from langchain.embeddings.openai import OpenAIEmbeddings
from vectordb import connect


async def run():
    dir = tempfile.mkdtemp(prefix="lancedb-")
    db = await connect(dir)
    table = await db.create_table("vectors", [{"vector": [0] * 1536, "text": "sample", "id": 1}])

    vector_store = await LanceDB.from_texts(
        ["Hello world", "Bye bye", "hello nice world"],
        [{"id": 2}, {"id": 1}, {"id": 3}],
        OpenAIEmbeddings(),
        table=table,
    )

    result_one = await vector_store.similarity_search("hello world", 1)
    print(result_one)
    # [ Document(page_content='hello nice world', metadata={'id': 3}) ]


# Run the function
import asyncio

asyncio.run(run())
```

API Reference:

- `LanceDB` from `@langchain/community/vectorstores/lancedb`
- `OpenAIEmbeddings` from `@langchain/openai`

### Create a new index from a loader

```python
import os
import tempfile
from langchain.vectorstores import LanceDB
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders.fs import TextLoader
from vectordb import connect

# Create docs with a loader
loader = TextLoader("src/document_loaders/example_data/example.txt")
docs = loader.load()


async def run():
    dir = tempfile.mkdtemp(prefix="lancedb-")
    db = await connect(dir)
    table = await db.create_table("vectors", [{"vector": [0] * 1536, "text": "sample", "source": "a"}])

    vector_store = await LanceDB.from_documents(docs, OpenAIEmbeddings(), table=table)

    result_one = await vector_store.similarity_search("hello world", 1)
    print(result_one)
    # [
    #   Document(page_content='Foo\nBar\nBaz\n\n', metadata={'source': 'src/document_loaders/example_data/example.txt'})
    # ]


# Run the function
import asyncio

asyncio.run(run())
```

API Reference:

- `LanceDB` from `@langchain/community/vectorstores/lancedb`
- `OpenAIEmbeddings` from `@langchain/openai`
- `TextLoader` from `langchain/document_loaders/fs/text`

### Open an existing dataset

```python
import os
import tempfile
from langchain.vectorstores import LanceDB
from langchain.embeddings.openai import OpenAIEmbeddings
from vectordb import connect


async def run():
    uri = await create_test_db()
    db = await connect(uri)
    table = await db.open_table("vectors")

    vector_store = LanceDB(OpenAIEmbeddings(), table=table)

    result_one = await vector_store.similarity_search("hello world", 1)
    print(result_one)
    # [ Document(page_content='Hello world', metadata={'id': 1}) ]


async def create_test_db():
    dir = tempfile.mkdtemp(prefix="lancedb-")
    db = await connect(dir)
    await db.create_table(
        "vectors",
        [
            {"vector": [0] * 1536, "text": "Hello world", "id": 1},
            {"vector": [0] * 1536, "text": "Bye bye", "id": 2},
            {"vector": [0] * 1536, "text": "hello nice world", "id": 3},
        ],
    )
    return dir


# Run the function
import asyncio

asyncio.run(run())
```

API Reference:

- `LanceDB` from `@langchain/community/vectorstores/lancedb`
- `OpenAIEmbeddings` from `@langchain/openai`
