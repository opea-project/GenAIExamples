# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

import yaml
from generate_helm_values import generate_helm_values


def run_kubectl_command(command):
    """Run a kubectl command and return the output."""
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\n{e.stderr}")
        exit(1)


def get_all_nodes():
    """Get the list of all nodes in the Kubernetes cluster."""
    command = ["kubectl", "get", "nodes", "-o", "json"]
    output = run_kubectl_command(command)
    nodes = json.loads(output)
    return [node["metadata"]["name"] for node in nodes["items"]]


def add_label_to_node(node_name, label):
    """Add a label to the specified node."""
    command = ["kubectl", "label", "node", node_name, label, "--overwrite"]
    print(f"Labeling node {node_name} with {label}...")
    run_kubectl_command(command)
    print(f"Label {label} added to node {node_name} successfully.")


def add_labels_to_nodes(node_count=None, label=None, node_names=None):
    """Add a label to the specified number of nodes or to specified nodes."""

    if node_names:
        # Add label to the specified nodes
        for node_name in node_names:
            add_label_to_node(node_name, label)
    else:
        # Fetch the node list and label the specified number of nodes
        all_nodes = get_all_nodes()
        if node_count is None or node_count > len(all_nodes):
            print(f"Error: Node count exceeds the number of available nodes ({len(all_nodes)} available).")
            sys.exit(1)

        selected_nodes = all_nodes[:node_count]
        for node_name in selected_nodes:
            add_label_to_node(node_name, label)


def clear_labels_from_nodes(label, node_names=None):
    """Clear the specified label from specific nodes if provided, otherwise from all nodes."""
    label_key = label.split("=")[0]  # Extract key from 'key=value' format

    # If specific nodes are provided, use them; otherwise, get all nodes
    nodes_to_clear = node_names if node_names else get_all_nodes()

    for node_name in nodes_to_clear:
        # Check if the node has the label by inspecting its metadata
        command = ["kubectl", "get", "node", node_name, "-o", "json"]
        node_info = run_kubectl_command(command)
        node_metadata = json.loads(node_info)

        # Check if the label exists on this node
        labels = node_metadata["metadata"].get("labels", {})
        if label_key in labels:
            # Remove the label from the node
            command = ["kubectl", "label", "node", node_name, f"{label_key}-"]
            print(f"Removing label {label_key} from node {node_name}...")
            run_kubectl_command(command)
            print(f"Label {label_key} removed from node {node_name} successfully.")
        else:
            print(f"Label {label_key} not found on node {node_name}, skipping.")


def add_helm_repo(repo_name, repo_url):
    # Add the repo if it does not exist
    add_command = ["helm", "repo", "add", repo_name, repo_url]
    try:
        subprocess.run(add_command, check=True)
        print(f"Added Helm repo {repo_name} from {repo_url}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to add Helm repo {repo_name}: {e}")


def delete_helm_repo(repo_name):
    """Delete Helm repo if it exists."""
    command = ["helm", "repo", "remove", repo_name]
    try:
        subprocess.run(command, check=True)
        print(f"Deleted Helm repo {repo_name}.")
    except subprocess.CalledProcessError:
        print(f"Failed to delete Helm repo {repo_name}. It may not exist.")


def install_helm_release(release_name, chart_name, namespace, values_file, device_type):
    """Deploy a Helm release with a specified name and chart.

    Parameters:
    - release_name: The name of the Helm release.
    - chart_name: The Helm chart name or path, e.g., "opea/chatqna".
    - namespace: The Kubernetes namespace for deployment.
    - values_file: The user values file for deployment.
    - device_type: The device type (e.g., "gaudi") for specific configurations (optional).
    """

    # Check if the namespace exists; if not, create it
    try:
        # Check if the namespace exists
        command = ["kubectl", "get", "namespace", namespace]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Namespace does not exist, create it
        print(f"Namespace '{namespace}' does not exist. Creating it...")
        command = ["kubectl", "create", "namespace", namespace]
        subprocess.run(command, check=True)
        print(f"Namespace '{namespace}' created successfully.")

    # Handle gaudi-specific values file if device_type is "gaudi"
    hw_values_file = None
    untar_dir = None
    if device_type == "gaudi":
        print("Device type is gaudi. Pulling Helm chart to get gaudi-values.yaml...")

        # Pull and untar the chart
        subprocess.run(["helm", "pull", chart_name, "--untar"], check=True)

        # Determine the directory name (get the actual chart_name if chart_name is in the format 'repo_name/chart_name', else use chart_name directly)
        chart_dir_name = chart_name.split("/")[-1] if "/" in chart_name else chart_name

        # Find the untarred directory (assumes only one directory matches chart_dir_name)
        untar_dirs = glob.glob(f"{chart_dir_name}*")
        if untar_dirs:
            untar_dir = untar_dirs[0]
            hw_values_file = os.path.join(untar_dir, "gaudi-values.yaml")
            print("gaudi-values.yaml pulled and ready for use.")
        else:
            print(f"Error: Could not find untarred directory for {chart_name}")
            return

    # Prepare the Helm install command
    command = ["helm", "install", release_name, chart_name, "--namespace", namespace]

    # Append additional values file for gaudi if it exists
    if hw_values_file:
        command.extend(["-f", hw_values_file])

    # Append the main values file
    command.extend(["-f", values_file])

    # Execute the Helm install command
    try:
        print(f"Running command: {' '.join(command)}")  # Print full command for debugging
        subprocess.run(command, check=True)
        print("Deployment initiated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while deploying Helm release: {e}")

    # Cleanup: Remove the untarred directory
    if untar_dir and os.path.isdir(untar_dir):
        print(f"Removing temporary directory: {untar_dir}")
        shutil.rmtree(untar_dir)
        print("Temporary directory removed successfully.")


def uninstall_helm_release(release_name, namespace=None):
    """Uninstall a Helm release and clean up resources, optionally delete the namespace if not 'default'."""
    # Default to 'default' namespace if none is specified
    if not namespace:
        namespace = "default"

    try:
        # Uninstall the Helm release
        command = ["helm", "uninstall", release_name, "--namespace", namespace]
        print(f"Uninstalling Helm release {release_name} in namespace {namespace}...")
        run_kubectl_command(command)
        print(f"Helm release {release_name} uninstalled successfully.")

        # If the namespace is specified and not 'default', delete it
        if namespace != "default":
            print(f"Deleting namespace {namespace}...")
            delete_namespace_command = ["kubectl", "delete", "namespace", namespace]
            run_kubectl_command(delete_namespace_command)
            print(f"Namespace {namespace} deleted successfully.")
        else:
            print("Namespace is 'default', skipping deletion.")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while uninstalling Helm release or deleting namespace: {e}")


def main():
    parser = argparse.ArgumentParser(description="Manage Helm Deployment.")
    parser.add_argument(
        "--release-name",
        type=str,
        default="chatqna",
        help="The Helm release name created during deployment (default: chatqna).",
    )
    parser.add_argument(
        "--chart-name",
        type=str,
        default="opea/chatqna",
        help="The chart name to deploy, composed of repo name and chart name (default: opea/chatqna).",
    )
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace (default: default).")
    parser.add_argument("--hf-token", help="Hugging Face API token.")
    parser.add_argument(
        "--model-dir", help="Model directory, mounted as volumes for service access to pre-downloaded models"
    )
    parser.add_argument("--repo-name", default="opea", help="Helm repo name to add/delete (default: opea).")
    parser.add_argument(
        "--repo-url",
        default="https://opea-project.github.io/GenAIInfra",
        help="Helm repository URL (default: https://opea-project.github.io/GenAIInfra).",
    )
    parser.add_argument("--user-values", help="Path to a user-specified values.yaml file.")
    parser.add_argument(
        "--create-values-only", action="store_true", help="Only create the values.yaml file without deploying."
    )
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the Helm release.")
    parser.add_argument("--num-nodes", type=int, default=1, help="Number of nodes to use (default: 1).")
    parser.add_argument("--node-names", nargs="*", help="Optional specific node names to label.")
    parser.add_argument("--add-label", action="store_true", help="Add label to specified nodes if this flag is set.")
    parser.add_argument(
        "--delete-label", action="store_true", help="Delete label from specified nodes if this flag is set."
    )
    parser.add_argument(
        "--label", default="node-type=opea-benchmark", help="Label to add/delete (default: node-type=opea-benchmark)."
    )
    parser.add_argument("--with-rerank", action="store_true", help="Include rerank service in the deployment.")
    parser.add_argument(
        "--tuned",
        action="store_true",
        help="Modify resources for services and change extraCmdArgs when creating values.yaml.",
    )
    parser.add_argument("--add-repo", action="store_true", help="Add the Helm repo specified by --repo-url.")
    parser.add_argument("--delete-repo", action="store_true", help="Delete the Helm repo specified by --repo-name.")
    parser.add_argument(
        "--device-type",
        type=str,
        choices=["cpu", "gaudi"],
        default="gaudi",
        help="Specify the device type for deployment (choices: 'cpu', 'gaudi'; default: gaudi).",
    )

    args = parser.parse_args()

    # Adjust num-nodes based on node-names if specified
    if args.node_names:
        num_node_names = len(args.node_names)
        if args.num_nodes != 1 and args.num_nodes != num_node_names:
            parser.error("--num-nodes must match the number of --node-names if both are specified.")
        else:
            args.num_nodes = num_node_names

    # Helm repository management
    if args.add_repo:
        add_helm_repo(args.repo_name, args.repo_url)
        return
    elif args.delete_repo:
        delete_helm_repo(args.repo_name)
        return

    # Node labeling management
    if args.add_label:
        add_labels_to_nodes(args.num_nodes, args.label, args.node_names)
        return
    elif args.delete_label:
        clear_labels_from_nodes(args.label, args.node_names)
        return

    # Uninstall Helm release if specified
    if args.uninstall:
        uninstall_helm_release(args.release_name, args.namespace)
        return

    # Prepare values.yaml if not uninstalling
    if args.user_values:
        values_file_path = args.user_values
    else:
        if not args.hf_token:
            parser.error("--hf-token are required")
        node_selector = {args.label.split("=")[0]: args.label.split("=")[1]}
        values_file_path = generate_helm_values(
            with_rerank=args.with_rerank,
            num_nodes=args.num_nodes,
            hf_token=args.hf_token,
            model_dir=args.model_dir,
            node_selector=node_selector,
            tune=args.tuned,
        )

    # Read back the generated YAML file for verification
    with open(values_file_path, "r") as file:
        print("Generated YAML contents:")
        print(file.read())

    # Deploy unless --create-values-only is specified
    if not args.create_values_only:
        install_helm_release(args.release_name, args.chart_name, args.namespace, values_file_path, args.device_type)


if __name__ == "__main__":
    main()
