# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import yaml


def generate_helm_values(with_rerank, num_nodes, hf_token, model_dir, node_selector=None, tune=False):
    """Create a values.yaml file based on the provided configuration."""

    # Log the received parameters
    print("Received parameters:")
    print(f"with_rerank: {with_rerank}")
    print(f"num_nodes: {num_nodes}")
    print(f"node_selector: {node_selector}")  # Log the node_selector
    print(f"tune: {tune}")

    if node_selector is None:
        node_selector = {}

    # Construct the base values dictionary
    values = {
        "tei": {"nodeSelector": {key: value for key, value in node_selector.items()}},
        "tgi": {"nodeSelector": {key: value for key, value in node_selector.items()}},
        "data-prep": {"nodeSelector": {key: value for key, value in node_selector.items()}},
        "redis-vector-db": {"nodeSelector": {key: value for key, value in node_selector.items()}},
        "retriever-usvc": {"nodeSelector": {key: value for key, value in node_selector.items()}},
        "chatqna-ui": {"nodeSelector": {key: value for key, value in node_selector.items()}},
        "global": {
            "HUGGINGFACEHUB_API_TOKEN": hf_token,  # Use passed token
            "modelUseHostPath": model_dir,  # Use passed model directory
        },
        "nodeSelector": {key: value for key, value in node_selector.items()},
    }

    if with_rerank:
        values["teirerank"] = {"nodeSelector": {key: value for key, value in node_selector.items()}}
    else:
        values["image"] = {"repository": "opea/chatqna-without-rerank"}
        values["teirerank"] = {"enabled": False}

    default_replicas = [
        {"name": "chatqna", "replicaCount": 2},
        {"name": "tei", "replicaCount": 1},
        {"name": "teirerank", "replicaCount": 1} if with_rerank else None,
        {"name": "tgi", "replicaCount": 7 if with_rerank else 8},
        {"name": "data-prep", "replicaCount": 1},
        {"name": "redis-vector-db", "replicaCount": 1},
        {"name": "retriever-usvc", "replicaCount": 2},
    ]

    if num_nodes > 1:
        # Scale replicas based on number of nodes
        replicas = [
            {"name": "chatqna", "replicaCount": 1 * num_nodes},
            {"name": "tei", "replicaCount": 1 * num_nodes},
            {"name": "teirerank", "replicaCount": 1} if with_rerank else None,
            {"name": "tgi", "replicaCount": (8 * num_nodes - 1) if with_rerank else 8 * num_nodes},
            {"name": "data-prep", "replicaCount": 1},
            {"name": "redis-vector-db", "replicaCount": 1},
            {"name": "retriever-usvc", "replicaCount": 1 * num_nodes},
        ]
    else:
        replicas = default_replicas

    # Remove None values for rerank disabled
    replicas = [r for r in replicas if r]

    # Update values.yaml with replicas
    for replica in replicas:
        service_name = replica["name"]
        if service_name == "chatqna":
            values["replicaCount"] = replica["replicaCount"]
            print(replica["replicaCount"])
        elif service_name in values:
            values[service_name]["replicaCount"] = replica["replicaCount"]

    # Prepare resource configurations based on tuning
    resources = []
    if tune:
        resources = [
            {
                "name": "chatqna",
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

        # Filter out any None values directly as part of initialization
        resources = [r for r in resources if r is not None]

        # Add resources for each service if tuning
        for resource in resources:
            service_name = resource["name"]
            if service_name == "chatqna":
                values["resources"] = resource["resources"]
            elif service_name in values:
                values[service_name]["resources"] = resource["resources"]

        # Add extraCmdArgs for tgi service with default values
        if "tgi" in values:
            values["tgi"]["extraCmdArgs"] = [
                "--max-input-length",
                "1280",
                "--max-total-tokens",
                "2048",
                "--max-batch-total-tokens",
                "65536",
                "--max-batch-prefill-tokens",
                "4096",
            ]

    yaml_string = yaml.dump(values, default_flow_style=False)

    # Determine the mode based on the 'tune' parameter
    mode = "tuned" if tune else "oob"

    # Determine the filename based on 'with_rerank' and 'num_nodes'
    if with_rerank:
        filename = f"{mode}-{num_nodes}-gaudi-with-rerank-values.yaml"
    else:
        filename = f"{mode}-{num_nodes}-gaudi-without-rerank-values.yaml"

    # Write the YAML data to the file
    with open(filename, "w") as file:
        file.write(yaml_string)

    # Get the current working directory and construct the file path
    current_dir = os.getcwd()
    filepath = os.path.join(current_dir, filename)

    print(f"YAML file {filepath} has been generated.")
    return filepath  # Optionally return the file path


# Main execution for standalone use of create_values_yaml
if __name__ == "__main__":
    # Example values for standalone execution
    with_rerank = True
    num_nodes = 2
    hftoken = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    modeldir = "/mnt/model"
    node_selector = {"node-type": "opea-benchmark"}
    tune = True

    filename = generate_helm_values(with_rerank, num_nodes, hftoken, modeldir, node_selector, tune)

    # Read back the generated YAML file for verification
    with open(filename, "r") as file:
        print("Generated YAML contents:")
        print(file.read())
