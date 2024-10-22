# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import subprocess

import yaml


def generate_yaml(num_nodes, mode="oob", with_rerank="True"):

    common_pods = [
        "chatqna-backend-server-deploy",
        "embedding-dependency-deploy",
        "dataprep-deploy",
        "vector-db",
        "retriever-deploy",
    ]

    if with_rerank:
        pods_list = common_pods + ["reranking-dependency-deploy", "llm-dependency-deploy"]
    else:
        pods_list = common_pods + ["llm-dependency-deploy"]

    if num_nodes == 1:
        replicas = [
            {"name": "chatqna-backend-server-deploy", "replicas": 2},
            {"name": "embedding-dependency-deploy", "replicas": 1},
            {"name": "reranking-dependency-deploy", "replicas": 1} if with_rerank else None,
            {"name": "llm-dependency-deploy", "replicas": 7 if with_rerank else 8},
            {"name": "dataprep-deploy", "replicas": 1},
            {"name": "vector-db", "replicas": 1},
            {"name": "retriever-deploy", "replicas": 2},
        ]
    else:
        replicas = [
            {"name": "chatqna-backend-server-deploy", "replicas": 1 * num_nodes},
            {"name": "embedding-dependency-deploy", "replicas": 1 * num_nodes},
            {"name": "reranking-dependency-deploy", "replicas": 1} if with_rerank else None,
            {"name": "llm-dependency-deploy", "replicas": (8 * num_nodes) - 1 if with_rerank else 8 * num_nodes},
            {"name": "dataprep-deploy", "replicas": 1},
            {"name": "vector-db", "replicas": 1},
            {"name": "retriever-deploy", "replicas": 1 * num_nodes},
        ]

    resources = [
        {
            "name": "chatqna-backend-server-deploy",
            "resources": {"limits": {"cpu": "16", "memory": "8000Mi"}, "requests": {"cpu": "16", "memory": "8000Mi"}},
        },
        {
            "name": "embedding-dependency-deploy",
            "resources": {"limits": {"cpu": "80", "memory": "20000Mi"}, "requests": {"cpu": "80", "memory": "20000Mi"}},
        },
        (
            {"name": "reranking-dependency-deploy", "resources": {"limits": {"habana.ai/gaudi": 1}}}
            if with_rerank
            else None
        ),
        {"name": "llm-dependency-deploy", "resources": {"limits": {"habana.ai/gaudi": 1}}},
        {"name": "retriever-deploy", "resources": {"requests": {"cpu": "16", "memory": "8000Mi"}}},
    ]

    replicas = [replica for replica in replicas if replica]
    resources = [resource for resource in resources if resource]

    tgi_params = [
        {
            "name": "llm-dependency-deploy",
            "args": [
                {"name": "--model-id", "value": '$(LLM_MODEL_ID)'},
                {"name": "--max-input-length", "value": 1280},
                {"name": "--max-total-tokens", "value": 2048},
                {"name": "--max-batch-total-tokens", "value": 35536},
                {"name": "--max-batch-prefill-tokens", "value": 4096},
            ],
        },
    ]

    replicas_dict = {item["name"]: item["replicas"] for item in replicas}
    resources_dict = {item["name"]: item["resources"] for item in resources}
    tgi_params_dict = {item["name"]: item["args"] for item in tgi_params}

    dicts_to_check = [
        {"dict": replicas_dict, "key": "replicas"},
    ]
    if mode == "tuned":
        dicts_to_check.extend([{"dict": resources_dict, "key": "resources"}, {"dict": tgi_params_dict, "key": "args"}])

    merged_specs = {"podSpecs": []}

    for pod in pods_list:
        pod_spec = {"name": pod}

        for item in dicts_to_check:
            if pod in item["dict"]:
                pod_spec[item["key"]] = item["dict"][pod]

        if len(pod_spec) > 1:
            merged_specs["podSpecs"].append(pod_spec)

    yaml_data = yaml.dump(merged_specs, default_flow_style=False)

    print(yaml_data)

    if with_rerank:
        filename = f"{mode}_{num_nodes}_gaudi_with_rerank.yaml"
    else:
        filename = f"{mode}_{num_nodes}_gaudi_without_rerank.yaml"
    with open(filename, "w") as file:
        file.write(yaml_data)

    current_dir = os.getcwd()
    filepath = os.path.join(current_dir, filename)
    print(f"YAML file {filepath} has been generated.")

    return filepath


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="The name of example pipelines", default="chatqna")
    parser.add_argument("--folder", help="The path of helmcharts folder", default=".")
    parser.add_argument(
        "--num_nodes", help="Number of nodes to deploy", type=int, choices=[1, 2, 4, 8], default=1, required=True
    )
    parser.add_argument(
        "--mode", help="set up your chatqna in the specified mode", type=str, choices=["oob", "tuned"], default="oob"
    )
    parser.add_argument(
        "--workflow",
        help="with rerank in the pipeline",
        type=str,
        choices=["with_rerank", "without_rerank"],
        default="with_rerank",
    )

    parser.add_argument("--template", help="helm template", action="store_true")
    args = parser.parse_args()

    if args.workflow == "with_rerank":
        with_rerank = True
        workflow_file = "./hpu_with_rerank.yaml"
    else:
        with_rerank = False
        workflow_file = "./hpu_without_rerank.yaml"

    customize_filepath = generate_yaml(args.num_nodes, mode=args.mode, with_rerank=with_rerank)

    if args.template:
        subprocess.run(
            ["helm", "template", args.folder, "-f", workflow_file, "-f", customize_filepath],
            check=True,
            text=True,
            capture_output=False,
        )
    else:
        subprocess.run(
            ["helm", "install", args.name, args.folder, "-f", workflow_file, "-f", customize_filepath],
            check=True,
            text=True,
            capture_output=False,
        )


if __name__ == "__main__":
    main()
