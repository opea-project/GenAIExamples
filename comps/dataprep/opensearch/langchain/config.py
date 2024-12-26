# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# Embedding model
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

# OpenSearch Connection Information
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 9200))
OPENSEARCH_INITIAL_ADMIN_PASSWORD = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "")


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


def format_opensearch_conn_from_env():
    opensearch_url = os.getenv("OPENSEARCH_URL", None)
    if opensearch_url:
        return opensearch_url
    else:
        using_ssl = get_boolean_env_var("OPENSEARCH_SSL", False)
        start = "https://" if using_ssl else "http://"

        return start + f"{OPENSEARCH_HOST}:{OPENSEARCH_PORT}"


OPENSEARCH_URL = format_opensearch_conn_from_env()

# Vector Index Configuration
INDEX_NAME = os.getenv("INDEX_NAME", "rag-opensearch")
KEY_INDEX_NAME = os.getenv("KEY_INDEX_NAME", "file-keys")

TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", 600))

SEARCH_BATCH_SIZE = int(os.getenv("SEARCH_BATCH_SIZE", 10))
