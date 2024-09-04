# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os


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


# VDMS Connection Information
VDMS_HOST = os.getenv("VDMS_HOST", "localhost")
VDMS_PORT = int(os.getenv("VDMS_PORT", 55555))


# def format_vdms_conn_from_env():
#     vdms_url = os.getenv("VDMS_URL", None)
#     if vdms_url:
#         return vdms_url
#     else:
#         using_ssl = get_boolean_env_var("VDMS_SSL", False)
#         start = "vdmss://" if using_ssl else "vdms://"

#         # if using RBAC
#         password = os.getenv("VDMS_PASSWORD", None)
#         username = os.getenv("VDMS_USERNAME", "default")
#         if password is not None:
#             start += f"{username}:{password}@"

#         return start + f"{VDMS_HOST}:{VDMS_PORT}"


# VDMS_URL = format_vdms_conn_from_env()

# Vector Index Configuration
INDEX_NAME = os.getenv("INDEX_NAME", "rag-vdms")
# HUGGINGFACEHUB_API_TOKEN ="dummy-token"


# current_file_path = os.path.abspath(__file__)
# parent_dir = os.path.dirname(current_file_path)
# VDMS_SCHEMA = os.getenv("VDMS_SCHEMA", "vdms_schema.yml")
# INDEX_SCHEMA = os.path.join(parent_dir, VDMS_SCHEMA)
SEARCH_ENGINE = "FaissFlat"
DISTANCE_STRATEGY = "L2"
