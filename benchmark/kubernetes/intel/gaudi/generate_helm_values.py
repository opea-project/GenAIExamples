# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from enum import Enum, auto

import yaml


class AIExample(Enum):
    CHATQNA = "chatqna"
    DOCSUM = "docsum"
    FAQGEN = "faqgen"
    CODEGEN = "codegen"
    CODETRANS = "codetrans"

    @staticmethod
    def from_string(value: str):
        """Convert lowercase string to AIExample."""
        for example in AIExample:
            if example.value == value:
                return example
        raise ValueError(f"Invalid example type: {value}")

def get_example_services(example_type):
    """Get service configuration for different AI examples."""
    COMMON_SERVICES = {
        "tgi": {"scalable": True},
        "llm-uservice": {"scalable": True},
    }

    EXAMPLE_CONFIGS = {
        AIExample.CHATQNA: {
            "services": {
                "tei": {"scalable": True},
                "tgi": {"scalable": True},
                "data-prep": {"scalable": False},
                "redis-vector-db": {"scalable": False},
                "retriever-usvc": {"scalable": True},
                "chatqna-ui": {"scalable": False},
            },
            "supports_rerank": True
        },
        AIExample.DOCSUM: {
            "services": {
                **COMMON_SERVICES,
                "whisper": {"scalable": True},
                "docsum-ui": {"scalable": False},
            },
            "supports_rerank": False
        },
        AIExample.FAQGEN: {
            "services": {
                **COMMON_SERVICES,
                "faqgen-ui": {"scalable": False},
            },
            "supports_rerank": False
        },
        AIExample.CODEGEN: {
            "services": {
                **COMMON_SERVICES,
                "codegen-ui": {"scalable": False},
            },
            "supports_rerank": False
        },
        AIExample.CODETRANS: {
            "services": {
                **COMMON_SERVICES,
                "codetrans-ui": {"scalable": False},
            },
            "supports_rerank": False
        }
    }

    return EXAMPLE_CONFIGS[example_type]

def configure_node_selectors(values, node_selector, example_config):
    """Configure node selectors for all services."""
    for service in example_config["services"].keys():
        values[service] = {"nodeSelector": {key: value for key, value in node_selector.items()}}
    values["nodeSelector"] = {key: value for key, value in node_selector.items()}
    return values

def configure_rerank(values, with_rerank, example_type_enum):
    """Configure rerank-specific settings."""
    if with_rerank:
        values["teirerank"] = {"nodeSelector": {key: value for key, value in values["nodeSelector"].items()}}
    elif example_type_enum == AIExample.CHATQNA:
        values["image"] = {"repository": "opea/chatqna-without-rerank"}
    return values

def get_replica_config(with_rerank, num_nodes, example_config, example_type_enum):
    """Get replica configuration based on example type and node count."""
    replicas = []

    # Check for the special case when num_nodes == 1 and example_type_enum is CHATQNA
    if num_nodes == 1 and example_type_enum == AIExample.CHATQNA:
        # Special handling for retriever-usvc and mega_backend when num_nodes is 1 and example_type_enum is CHATQNA
        replicas.append({
            "name": "retriever-usvc",
            "replicaCount": 2
        })
        replicas.append({
            "name": "mega_backend",
            "replicaCount": 2
        })
        # Add rerank service if supported and enabled
        if example_config["supports_rerank"] and with_rerank:
            replicas.append({
                "name": "teirerank",
                "replicaCount": 1
            })
            replicas.append({
                "name": "tgi",
                "replicaCount": 7
            })
    else:
        # Proceed with normal logic for num_nodes > 1 or any other condition
        for service_name, config in example_config["services"].items():
            if service_name == "tgi":
                # Special handling for TGI service
                if example_config["supports_rerank"] and with_rerank:
                    replica_count = (8 * num_nodes - 1)
                else:
                    replica_count = 8 * num_nodes
            else:
                # For other services, scale based on num_nodes if they're scalable
                replica_count = num_nodes if config.get("scalable", True) else 1

            replicas.append({
                "name": service_name,
                "replicaCount": replica_count
            })

        replicas.append({
            "name": "mega_backend",
            "replicaCount": num_nodes
        })

    return replicas

def get_output_filename(tune, num_nodes, with_rerank, example_type):
    """Generate output filename based on configuration."""
    mode = "tuned" if tune else "oob"
    rerank_suffix = "with-rerank-" if with_rerank else ""
    return f"{example_type}-{mode}-{num_nodes}-gaudi-{rerank_suffix}values.yaml"

def configure_resources(values, tune, with_rerank, example_type_enum):
    """Configure resources when tuning is enabled."""
    if not tune:
        return values

    # Only configure resources for CHATQNA example
    if example_type_enum != AIExample.CHATQNA:
        return values

    resource_configs = [
        {
            "name": "mega_backend",
            "resources": {
                "limits": {"cpu": "16", "memory": "8000Mi"},
                "requests": {"cpu": "16", "memory": "8000Mi"},
            },
        },
        {
            "name": "tei",
            "resources": {
                "limits": {"cpu": "80", "memory": "20000Mi"},
                "requests": {"cpu": "80", "memory": "20000Mi"},
            },
        },
        {"name": "teirerank", "resources": {"limits": {"habana.ai/gaudi": 1}}} if with_rerank else None,
        {"name": "tgi", "resources": {"limits": {"habana.ai/gaudi": 1}}},
        {"name": "retriever-usvc", "resources": {"requests": {"cpu": "8", "memory": "8000Mi"}}},
    ]

    for config in [r for r in resource_configs if r]:
        service_name = config["name"]
        if service_name == "mega_backend":
            values["resources"] = config["resources"]
        elif service_name in values:
            values[service_name]["resources"] = config["resources"]

    if "tgi" in values:
        values["tgi"]["extraCmdArgs"] = [
            "--max-input-length", "1280",
            "--max-total-tokens", "2048",
            "--max-batch-total-tokens", "65536",
            "--max-batch-prefill-tokens", "4096",
        ]

    return values

def generate_helm_values(example_type, with_rerank, num_nodes, hf_token, model_dir, node_selector=None, tune=False):
    """Create a values.yaml file based on the provided configuration."""
    print(f"Generating values for {example_type} example")
    print(f"with_rerank: {with_rerank}")
    print(f"num_nodes: {num_nodes}")
    print(f"node_selector: {node_selector}")
    print(f"tune: {tune}")

    # Convert example_type from string to AIExample enum
    try:
        example_type_enum = AIExample.from_string(example_type)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    example_config = get_example_services(example_type_enum)

    if node_selector is None:
        node_selector = {}

    # Initialize base values
    values = {
        "global": {
            "HUGGINGFACEHUB_API_TOKEN": hf_token,
            "modelUseHostPath": model_dir,
        }
    }

    # Apply configurations
    values = configure_node_selectors(values, node_selector, example_config)
    values = configure_rerank(values, with_rerank, example_type_enum)

    # Configure replicas
    replicas = get_replica_config(with_rerank, num_nodes, example_config, example_type_enum)
    for replica in replicas:
        service_name = replica["name"]
        if service_name == "mega_backend":
            values["replicaCount"] = replica["replicaCount"]
        elif service_name in values:
            values[service_name]["replicaCount"] = replica["replicaCount"]

    # Configure resources
    values = configure_resources(values, tune, with_rerank, example_type_enum)

    # Generate and write YAML file
    filename = get_output_filename(tune, num_nodes, with_rerank, example_type)
    yaml_string = yaml.dump(values, default_flow_style=False)

    # Write the YAML data to the file
    with open(filename, "w") as file:
        file.write(yaml_string)

    # Get the current working directory and construct the file path
    current_dir = os.getcwd()
    filepath = os.path.join(current_dir, filename)

    print(f"YAML file {filepath} has been generated.")
    return {"status": "success", "filepath": filepath}

# Main execution for standalone use of create_values_yaml
if __name__ == "__main__":
    # Example values for standalone execution
    example_type = "docsum"
    with_rerank = False
    num_nodes = 2
    hftoken = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    modeldir = "/mnt/model"
    node_selector = {"node-type": "opea-benchmark"}
    tune = False

    result = generate_helm_values(example_type, with_rerank, num_nodes, hftoken, modeldir, node_selector, tune)

    # Read back the generated YAML file for verification
    with open(result["filepath"], "r") as file:
        print("Generated YAML contents:")
        print(file.read())
