# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from enum import Enum, auto

import yaml

################################################################################
#                                                                              #
#                        HELM VALUES GENERATION SECTION                        #
#                                                                              #
################################################################################


def configure_node_selectors(values, node_selector, deploy_config):
    """Configure node selectors for all services."""
    for service_name, config in deploy_config["services"].items():
        if service_name == "backend":
            values["nodeSelector"] = {key: value for key, value in node_selector.items()}
        elif service_name == "llm":
            engine = config.get("engine", "tgi")
            values[engine] = {"nodeSelector": {key: value for key, value in node_selector.items()}}
        else:
            values[service_name] = {"nodeSelector": {key: value for key, value in node_selector.items()}}
    return values


def configure_replica(values, deploy_config):
    """Get replica configuration based on example type and node count."""
    for service_name, config in deploy_config["services"].items():
        if not config.get("replicaCount"):
            continue

        if service_name == "llm":
            engine = config.get("engine", "tgi")
            values[engine]["replicaCount"] = config["replicaCount"]
        elif service_name == "backend":
            values["replicaCount"] = config["replicaCount"]
        else:
            values[service_name]["replicaCount"] = config["replicaCount"]

    return values


def get_output_filename(num_nodes, with_rerank, example_type, device, action_type, batch_size=None):
    """Generate output filename based on configuration."""
    rerank_suffix = "with-rerank-" if with_rerank else ""
    action_suffix = "deploy-" if action_type == 0 else "update-" if action_type == 1 else ""
    # Only include batch_suffix if batch_size is not None
    batch_suffix = f"batch{batch_size}-" if batch_size else ""

    return f"{example_type}-{rerank_suffix}{device}-{action_suffix}node{num_nodes}-{batch_suffix}values.yaml"


def configure_resources(values, deploy_config):
    """Configure resources when tuning is enabled."""
    resource_configs = []

    for service_name, config in deploy_config["services"].items():
        # Skip if resources configuration doesn't exist or is not enabled
        resources_config = config.get("resources", {})
        if not resources_config:
            continue

        resources = {}
        if deploy_config["device"] == "gaudi" and resources_config.get("cards_per_instance", 0) > 1:
            resources = {
                "limits": {"habana.ai/gaudi": resources_config["cards_per_instance"]},
                "requests": {"habana.ai/gaudi": resources_config["cards_per_instance"]},
            }
        else:
            # Only add CPU if cores_per_instance has a valid value
            cores = resources_config.get("cores_per_instance")
            if cores is not None and cores != "":
                resources = {"limits": {"cpu": cores}, "requests": {"cpu": cores}}

            # Only add memory if memory_capacity has a valid value
            memory = resources_config.get("memory_capacity")
            if memory is not None and memory != "":
                if not resources:
                    resources = {"limits": {"memory": memory}, "requests": {"memory": memory}}
                else:
                    resources["limits"]["memory"] = memory
                    resources["requests"]["memory"] = memory

        if resources:
            if service_name == "llm":
                engine = config.get("engine", "tgi")
                resource_configs.append(
                    {
                        "name": engine,
                        "resources": resources,
                    }
                )
            else:
                resource_configs.append(
                    {
                        "name": service_name,
                        "resources": resources,
                    }
                )

    for config in [r for r in resource_configs if r]:
        service_name = config["name"]
        if service_name == "backend":
            values["resources"] = config["resources"]
        elif service_name in values:
            values[service_name]["resources"] = config["resources"]

    return values


def configure_extra_cmd_args(values, deploy_config):
    """Configure extra command line arguments for services."""
    batch_size = None
    for service_name, config in deploy_config["services"].items():
        if service_name == "llm":
            extra_cmd_args = []
            engine = config.get("engine", "tgi")
            model_params = config.get("model_params", {})

            # Get engine-specific parameters
            engine_params = model_params.get(engine, {})

            # Get batch parameters and token parameters configuration
            batch_params = engine_params.get("batch_params", {})
            token_params = engine_params.get("token_params", {})

            # Get batch size based on engine type
            if engine == "tgi":
                batch_size = batch_params.get("max_batch_size")
            elif engine == "vllm":
                batch_size = batch_params.get("max_num_seqs")
            batch_size = batch_size if batch_size and batch_size != "" else None

            # Add all parameters that exist in batch_params
            for param, value in batch_params.items():
                if value is not None and value != "":
                    extra_cmd_args.extend([f"--{param.replace('_', '-')}", str(value)])

            # Add all parameters that exist in token_params
            for param, value in token_params.items():
                if value is not None and value != "":
                    extra_cmd_args.extend([f"--{param.replace('_', '-')}", str(value)])

            if extra_cmd_args:
                if engine not in values:
                    values[engine] = {}
                values[engine]["extraCmdArgs"] = extra_cmd_args
                print(f"extraCmdArgs: {extra_cmd_args}")

    return values, batch_size


def configure_models(values, deploy_config):
    """Configure model settings for services."""
    for service_name, config in deploy_config["services"].items():
        # Get model_id and check if it's valid (not None or empty string)
        model_id = config.get("model_id")
        if not model_id or model_id == "" or config.get("enabled") is False:
            continue

        if service_name == "llm":
            # For LLM service, use its engine as the key
            # Check if engine is valid (not None or empty string)
            engine = config.get("engine", "tgi")
            if engine and engine != "":
                values[engine]["LLM_MODEL_ID"] = model_id
        elif service_name == "tei":
            values[service_name]["EMBEDDING_MODEL_ID"] = model_id
        elif service_name == "teirerank":
            values[service_name]["RERANK_MODEL_ID"] = model_id

    return values


def configure_rerank(values, with_rerank, deploy_config, example_type, node_selector):
    """Configure rerank service."""
    if with_rerank:
        if "teirerank" not in values:
            values["teirerank"] = {"nodeSelector": {key: value for key, value in node_selector.items()}}
        elif "nodeSelector" not in values["teirerank"]:
            values["teirerank"]["nodeSelector"] = {key: value for key, value in node_selector.items()}
    else:
        if example_type == "chatqna":
            values["image"] = {"repository": "opea/chatqna-without-rerank"}
        if "teirerank" not in values:
            values["teirerank"] = {"enabled": False}
        elif "enabled" not in values["teirerank"]:
            values["teirerank"]["enabled"] = False
    return values


def generate_helm_values(example_type, deploy_config, chart_dir, action_type, node_selector=None):
    """Create a values.yaml file based on the provided configuration."""
    if deploy_config is None:
        raise ValueError("deploy_config is required")

    # Ensure the chart_dir exists
    if not os.path.exists(chart_dir):
        return {"status": "false", "message": f"Chart directory {chart_dir} does not exist"}

    num_nodes = deploy_config.get("node", 1)
    with_rerank = deploy_config["services"].get("teirerank", {}).get("enabled", False)

    print(f"Generating values for {example_type} example")
    print(f"with_rerank: {with_rerank}")
    print(f"num_nodes: {num_nodes}")
    print(f"node_selector: {node_selector}")

    # Initialize base values
    values = {
        "global": {
            "HUGGINGFACEHUB_API_TOKEN": deploy_config.get("HUGGINGFACEHUB_API_TOKEN", ""),
            "modelUseHostPath": deploy_config.get("modelUseHostPath", ""),
        }
    }

    # Configure components
    values = configure_node_selectors(values, node_selector or {}, deploy_config)
    values = configure_rerank(values, with_rerank, deploy_config, example_type, node_selector or {})
    values = configure_replica(values, deploy_config)
    values = configure_resources(values, deploy_config)
    values, batch_size = configure_extra_cmd_args(values, deploy_config)
    values = configure_models(values, deploy_config)

    device = deploy_config.get("device", "unknown")

    # Generate and write YAML file
    filename = get_output_filename(num_nodes, with_rerank, example_type, device, action_type, batch_size)
    yaml_string = yaml.dump(values, default_flow_style=False)

    filepath = os.path.join(chart_dir, filename)

    # Write the YAML data to the file
    with open(filepath, "w") as file:
        file.write(yaml_string)

    print(f"YAML file {filepath} has been generated.")
    return {"status": "success", "filepath": filepath}


################################################################################
#                                                                              #
#                            DEPLOYMENT SECTION                                #
#                                                                              #
################################################################################


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


def get_hw_values_file(deploy_config, chart_dir):
    """Get the hardware-specific values file based on the deploy configuration."""
    device_type = deploy_config.get("device", "cpu")
    print(f"Device type is {device_type}. Using existing Helm chart values files...")
    if device_type == "cpu":
        print(f"Device type is {device_type}. Using existing Helm chart values files.")
        return None

    llm_engine = deploy_config.get("services", {}).get("llm", {}).get("engine", "tgi")
    version = deploy_config.get("version", "1.1.0")

    if os.path.isdir(chart_dir):
        # Determine which values file to use based on version
        if version in ["1.0.0", "1.1.0"]:
            hw_values_file = os.path.join(chart_dir, f"{device_type}-values.yaml")
        else:
            hw_values_file = os.path.join(chart_dir, f"{device_type}-{llm_engine}-values.yaml")

        if not os.path.exists(hw_values_file):
            print(f"Warning: {hw_values_file} not found")
            hw_values_file = None
        else:
            print(f"Device-specific values file found: {hw_values_file}")
    else:
        print(f"Error: Could not find directory for {chart_dir}")
        hw_values_file = None

    return hw_values_file


def install_helm_release(release_name, chart_name, namespace, hw_values_file, deploy_values_file):
    """Deploy a Helm release with a specified name and chart.

    Parameters:
    - release_name: The name of the Helm release.
    - chart_name: The Helm chart name or path.
    - namespace: The Kubernetes namespace for deployment.
    - hw_values_file: The values file for hw specific
    - deploy_values_file: The values file for deployment.
    """

    # Check if the namespace exists; if not, create it
    try:
        command = ["kubectl", "get", "namespace", namespace]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"Namespace '{namespace}' does not exist. Creating it...")
        command = ["kubectl", "create", "namespace", namespace]
        subprocess.run(command, check=True)
        print(f"Namespace '{namespace}' created successfully.")

    try:
        # Prepare the Helm install command
        command = ["helm", "install", release_name, chart_name, "--namespace", namespace]

        # Append values files in order
        if hw_values_file:
            command.extend(["-f", hw_values_file])
        if deploy_values_file:
            command.extend(["-f", deploy_values_file])

        # Execute the Helm install command
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
        print("Deployment initiated successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while deploying Helm release: {e}")


def uninstall_helm_release(release_name, namespace=None):
    """Uninstall a Helm release and clean up resources, optionally delete the namespace if not 'default'.

    First checks if the release exists before attempting to uninstall.
    """
    # Default to 'default' namespace if none is specified
    if not namespace:
        namespace = "default"

    try:
        # Check if the release exists
        check_command = ["helm", "list", "--namespace", namespace, "--filter", release_name, "--output", "json"]
        output = run_kubectl_command(check_command)
        releases = json.loads(output)

        if not releases:
            print(f"Helm release {release_name} not found in namespace {namespace}. Nothing to uninstall.")
            return

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
    except json.JSONDecodeError as e:
        print(f"Error parsing helm list output: {e}")


def update_service(release_name, chart_name, namespace, hw_values_file, deploy_values_file, update_values_file):
    """Update the deployment using helm upgrade with new values.

    Args:
        release_name: The helm release name
        namespace: The kubernetes namespace
        deploy_config: The deployment configuration
        chart_name: The chart name for the deployment
    """

    # Construct helm upgrade command
    command = [
        "helm",
        "upgrade",
        release_name,
        chart_name,
        "--namespace",
        namespace,
        "-f",
        hw_values_file,
        "-f",
        deploy_values_file,
        "-f",
        update_values_file,
    ]
    # Execute helm upgrade
    print(f"Running command: {' '.join(command)}")
    run_kubectl_command(command)
    print("Deployment updated successfully")


def read_deploy_config(config_path):
    """Read and parse the deploy config file.

    Args:
        config_path: Path to the deploy config file

    Returns:
        The parsed deploy config dictionary or None if failed
    """
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load deploy config: {str(e)}")
        return None


def check_deployment_ready(release_name, namespace, timeout=1000, interval=5, logfile="deployment.log"):
    """Wait until all pods in the deployment are running and ready.

    Args:
        namespace: The Kubernetes namespace
        timeout: The maximum time to wait in seconds (default 120 seconds)
        interval: The interval between checks in seconds (default 5 seconds)
        logfile: The file to log output to (default 'deployment.log')

    Returns:
        0 if success, 1 if failure (timeout reached)
    """
    try:
        # Get the list of deployments in the namespace
        cmd = ["kubectl", "-n", namespace, "get", "deployments", "-o", "jsonpath='{.items[*].metadata.name}'"]
        deployments_output = subprocess.check_output(cmd, text=True)
        deployments = deployments_output.strip().split()

        # Strip the first and last elements of single quotes if present
        deployments[0] = deployments[0].strip("'")
        deployments[-1] = deployments[-1].strip("'")

        with open(logfile, "a") as log:
            log.write(f"Found deployments: {', '.join(deployments)}\n")

        timer = 0

        # Loop through each deployment to check its readiness
        for deployment_name in deployments:

            if "-" not in deployment_name or "ui" in deployment_name or "nginx" in deployment_name:
                continue

            instance_name = deployment_name.split("-", 1)[0]
            app_name = deployment_name.split("-", 1)[1]

            if instance_name != release_name:
                continue

            cmd = ["kubectl", "-n", namespace, "get", "deployment", deployment_name, "-o", "jsonpath={.spec.replicas}"]
            desired_replicas = int(subprocess.check_output(cmd, text=True).strip())

            with open(logfile, "a") as log:
                log.write(f"Checking deployment '{deployment_name}' with desired replicas: {desired_replicas}\n")

            while True:
                cmd = [
                    "kubectl",
                    "-n",
                    namespace,
                    "get",
                    "pods",
                    "-l",
                    f"app.kubernetes.io/instance={instance_name}",
                    "-l",
                    f"app.kubernetes.io/name={app_name}",
                    "--field-selector=status.phase=Running",
                    "-o",
                    "json",
                ]

                pods_output = subprocess.check_output(cmd, text=True)
                pods = json.loads(pods_output)

                ready_pods = sum(
                    1
                    for pod in pods["items"]
                    if all(container.get("ready") for container in pod.get("status", {}).get("containerStatuses", []))
                )

                terminating_pods = sum(
                    1 for pod in pods["items"] if pod.get("metadata", {}).get("deletionTimestamp") is not None
                )

                with open(logfile, "a") as log:
                    log.write(
                        f"Ready pods: {ready_pods}, Desired replicas: {desired_replicas}, Terminating pods: {terminating_pods}\n"
                    )

                if ready_pods == desired_replicas and terminating_pods == 0:
                    with open(logfile, "a") as log:
                        log.write(f"All pods for deployment '{deployment_name}' are running and ready.\n")
                    break

                if timer >= timeout:
                    with open(logfile, "a") as log:
                        log.write(
                            f"Timeout reached for deployment '{deployment_name}'. Not all pods are running and ready.\n"
                        )
                    return 1  # Failure

                time.sleep(interval)
                timer += interval

        return 0  # Success for all deployments

    except subprocess.CalledProcessError as e:
        with open(logfile, "a") as log:
            log.write(f"Error executing kubectl command: {e}\n")
        return 1  # Failure
    except json.JSONDecodeError as e:
        with open(logfile, "a") as log:
            log.write(f"Error parsing kubectl output: {e}\n")
        return 1  # Failure
    except Exception as e:
        with open(logfile, "a") as log:
            log.write(f"Unexpected error: {e}\n")
        return 1  # Failure


def main():
    parser = argparse.ArgumentParser(description="Manage Helm Deployment.")
    parser.add_argument(
        "--chart-name",
        type=str,
        default="chatqna",
        help="The chart name to deploy (default: chatqna).",
    )
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace (default: default).")
    parser.add_argument("--user-values", help="Path to a user-specified values.yaml file.")
    parser.add_argument("--deploy-config", help="Path to a deploy config yaml file.")
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
    parser.add_argument("--update-service", action="store_true", help="Update the deployment with new configuration.")
    parser.add_argument("--check-ready", action="store_true", help="Check if all services in the deployment are ready.")
    parser.add_argument("--chart-dir", default=".", help="Path to the untarred Helm chart directory.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=1000,
        help="Maximum time to wait for deployment readiness in seconds (default: 1000)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval between readiness checks in seconds (default: 5)",
    )

    args = parser.parse_args()

    # Node labeling management
    if args.add_label:
        add_labels_to_nodes(args.num_nodes, args.label, args.node_names)
        return
    elif args.delete_label:
        clear_labels_from_nodes(args.label, args.node_names)
        return
    elif args.check_ready:
        is_ready = check_deployment_ready(args.chart_name, args.namespace, args.timeout, args.interval)
        return is_ready
    elif args.uninstall:
        uninstall_helm_release(args.chart_name, args.namespace)
        return

    # Load deploy_config if provided
    deploy_config = None
    if args.deploy_config:
        deploy_config = read_deploy_config(args.deploy_config)
        if deploy_config is None:
            parser.error("Failed to load deploy config")
            return

    hw_values_file = get_hw_values_file(deploy_config, args.chart_dir)

    action_type = 0
    if args.update_service:
        action_type = 1

    # The user file is provided for deploy when --update-service is not specified
    if args.user_values and not args.update_service:
        values_file_path = args.user_values
    else:
        if not args.deploy_config:
            parser.error("--deploy-config is required")

        node_selector = {args.label.split("=")[0]: args.label.split("=")[1]}

        print("go to generate deploy values" if action_type == 0 else "go to generate update values")

        # Generate values file for deploy or update service
        result = generate_helm_values(
            example_type=args.chart_name,
            deploy_config=deploy_config,
            chart_dir=args.chart_dir,
            action_type=action_type,  # 0 - deploy, 1 - update
            node_selector=node_selector,
        )

        # Check result status
        if result["status"] == "success":
            values_file_path = result["filepath"]
        else:
            parser.error(f"Failed to generate values.yaml: {result['message']}")
            return

    print("start to read the generated values file")
    # Read back the generated YAML file for verification
    with open(values_file_path, "r") as file:
        print("Generated YAML contents:")
        print(file.read())

    # Handle service update if specified
    if args.update_service:
        if not args.user_values:
            parser.error("--user-values is required for update reference")

        try:
            update_service(
                args.chart_name, args.chart_name, args.namespace, hw_values_file, args.user_values, values_file_path
            )
            print(f"values_file_path: {values_file_path}")
            return
        except Exception as e:
            parser.error(f"Failed to update deployment: {str(e)}")
            return

    # Deploy unless --create-values-only is specified
    if not args.create_values_only:
        install_helm_release(args.chart_name, args.chart_name, args.namespace, hw_values_file, values_file_path)
        print(f"values_file_path: {values_file_path}")


if __name__ == "__main__":
    main()
