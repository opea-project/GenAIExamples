# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os


#######################################################
#                Common Functions                     #
#######################################################
def get_boolean_env_var(var_name, default_value=False):
    """Retrieve the boolean value of an environment variable.

    Args:
    var_name (str): The name of the environment variable to retrieve.
    default_value (bool): The default value to return if the variable
    is not found.

    Returns:
    bool: The value of the environment variable, interpreted as a boolean.
    """
    true_values = {"true", "1", "t", "y", "yes"}
    false_values = {"false", "0", "f", "n", "no"}

    # Retrieve the environment variable's value
    value = os.getenv(var_name, "").lower()

    # Decide the boolean value based on the content of the string
    if value in true_values:
        return True
    elif value in false_values:
        return False
    else:
        return default_value


# Whether or not to enable langchain debugging
DEBUG = get_boolean_env_var("DEBUG", False)
# Set DEBUG env var to "true" if you wish to enable LC debugging module
if DEBUG:
    import langchain

    langchain.debug = True

# Embedding model
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "maidalun1020/bce-embedding-base_v1")
TEI_EMBEDDING_ENDPOINT = os.getenv("TEI_EMBEDDING_ENDPOINT")
BRIDGE_TOWER_EMBEDDING = os.getenv("BRIDGE_TOWER_EMBEDDING", False)

# Directory pathss
current_file_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(current_file_path)


#######################################################
#                Elasticsearch                        #
#######################################################
ES_CONNECTION_STRING = os.getenv("ES_CONNECTION_STRING", "http://localhost:9200")
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "rag_elasticsearch")


#######################################################
#                    Neo4j                            #
#######################################################
NEO4J_URL = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test")
host_ip = os.getenv("host_ip")
TGI_LLM_ENDPOINT = os.getenv("TGI_LLM_ENDPOINT", f"http://{host_ip}:6005")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o")


#######################################################
#                    Pathway                          #
#######################################################
PATHWAY_HOST = os.getenv("PATHWAY_HOST", "127.0.0.1")
PATHWAY_PORT = int(os.getenv("PATHWAY_PORT", 8666))


#######################################################
#                     Redis                           #
#######################################################
INDEX_NAME = os.getenv("INDEX_NAME", "rag_redis")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


def format_redis_conn_from_env():
    redis_url = os.getenv("REDIS_URL", None)
    if redis_url:
        return redis_url
    else:
        using_ssl = get_boolean_env_var("REDIS_SSL", False)
        start = "rediss://" if using_ssl else "redis://"

        # if using RBAC
        password = os.getenv("REDIS_PASSWORD", None)
        username = os.getenv("REDIS_USERNAME", "default")
        if password is not None:
            start += f"{username}:{password}@"

        return start + f"{REDIS_HOST}:{REDIS_PORT}"


REDIS_URL = format_redis_conn_from_env()
REDIS_SCHEMA = os.getenv("REDIS_SCHEMA", "redis_schema_multi.yml")
schema_path = os.path.join(parent_dir, REDIS_SCHEMA)
INDEX_SCHEMA = schema_path


#######################################################
#                     Milvus                          #
#######################################################
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", 19530))
MILVUS_URI = f"http://{MILVUS_HOST}:{MILVUS_PORT}"
INDEX_PARAMS = {"index_type": "FLAT", "metric_type": "IP", "params": {}}
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag_milvus")
# TEI configuration
TEI_EMBEDDING_MODEL = os.environ.get("TEI_EMBEDDING_MODEL", "/home/user/bce-embedding-base_v1")
TEI_EMBEDDING_ENDPOINT = os.environ.get("TEI_EMBEDDING_ENDPOINT", "")
os.environ["OPENAI_API_BASE"] = TEI_EMBEDDING_ENDPOINT
os.environ["OPENAI_API_KEY"] = "Dummy key"


#######################################################
#                   Opensearch                        #
#######################################################
# OpenSearch Connection Information
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 9200))
OPENSEARCH_INITIAL_ADMIN_PASSWORD = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "")


def format_opensearch_conn_from_env():
    opensearch_url = os.getenv("OPENSEARCH_URL", None)
    if opensearch_url:
        return opensearch_url
    else:
        using_ssl = get_boolean_env_var("OPENSEARCH_SSL", False)
        start = "https://" if using_ssl else "http://"

        return start + f"{OPENSEARCH_HOST}:{OPENSEARCH_PORT}"


OPENSEARCH_URL = format_opensearch_conn_from_env()
OPENSEARCH_INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", "rag_opensearch")


#######################################################
#                     Pinecone                        #
#######################################################
# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "xxx_xxx")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag_pinecone")


#######################################################
#                     PGvector                        #
#######################################################
PG_CONNECTION_STRING = os.getenv("PG_CONNECTION_STRING", "localhost")
PG_INDEX_NAME = os.getenv("PG_INDEX_NAME", "rag_pgvector")


#######################################################
#                        QDrant                       #
#######################################################
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_EMBED_DIMENSION = os.getenv("QDRANT_EMBED_DIMENSION", 768)
QDRANT_INDEX_NAME = os.getenv("QDRANT_INDEX_NAME", "rag_qdrant")


#######################################################
#                        VDMs                         #
#######################################################
# VDMS Connection Information
VDMS_HOST = os.getenv("VDMS_HOST", "localhost")
VDMS_PORT = int(os.getenv("VDMS_PORT", 55555))
VDMS_INDEX_NAME = os.getenv("VDMS_INDEX_NAME", "rag_vdms")
VDMS_USE_CLIP = int(os.getenv("VDMS_USE_CLIP", 0))
SEARCH_ENGINE = "FaissFlat"
DISTANCE_STRATEGY = "IP"
