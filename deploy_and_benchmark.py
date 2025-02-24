# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import copy
import os
import re
import shutil
import subprocess
import sys

import yaml

from benchmark import run_benchmark


def read_yaml(file_path):
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None


def construct_deploy_config(deploy_config, target_node, batch_param_value=None):
    """Construct a new deploy config based on the target node number and optional batch parameter value.

    Args:
        deploy_config: Original deploy config dictionary
        target_node: Target node number to match in the node array
        batch_param_value: Optional specific batch parameter value to use (max_batch_size for TGI or max_num_seqs for VLLM)

    Returns:
        A new deploy config with single values for node and instance_num
    """
    # Deep copy the original config to avoid modifying it
    new_config = copy.deepcopy(deploy_config)

    # Get the node array and validate
    nodes = deploy_config.get("node")
    if not isinstance(nodes, list):
        raise ValueError("deploy_config['node'] must be an array")

    # Find the index of the target node
    try:
        node_index = nodes.index(target_node)
    except ValueError:
        raise ValueError(f"Target node {target_node} not found in node array {nodes}")

    # Set the single node value
    new_config["node"] = target_node

    # First determine which llm replicaCount to use based on teirerank.enabled
    services = new_config.get("services", {})
    teirerank_enabled = services.get("teirerank", {}).get("enabled", True)

    if "llm" in services:
        llm_config = services["llm"]
        if isinstance(llm_config.get("replicaCount"), dict):
            replica_counts = llm_config["replicaCount"]
            llm_config["replicaCount"] = (
                replica_counts["with_teirerank"] if teirerank_enabled else replica_counts["without_teirerank"]
            )

    # Update instance_num for each service based on the same index
    for service_name, service_config in services.items():
        if "replicaCount" in service_config:
            instance_nums = service_config["replicaCount"]
            if isinstance(instance_nums, list):
                if len(instance_nums) != len(nodes):
                    raise ValueError(
                        f"instance_num array length ({len(instance_nums)}) for service {service_name} "
                        f"doesn't match node array length ({len(nodes)})"
                    )
                service_config["replicaCount"] = instance_nums[node_index]

    # Update batch parameter if specified
    if batch_param_value is not None and "llm" in new_config["services"]:
        llm_config = new_config["services"]["llm"]
        engine = llm_config.get("engine", "tgi")

        if engine == "tgi":
            llm_config["max_batch_size"] = batch_param_value
        elif engine == "vllm":
            llm_config["max_num_seqs"] = batch_param_value
            # Remove TGI-specific parameter if it exists
            llm_config.pop("max_batch_size", None)

    return new_config


def pull_helm_chart(chart_pull_url, version, chart_name):
    # Pull and untar the chart
    subprocess.run(["helm", "pull", chart_pull_url, "--version", version, "--untar"], check=True)

    current_dir = os.getcwd()
    untar_dir = os.path.join(current_dir, chart_name)

    if not os.path.isdir(untar_dir):
        print(f"Error: Could not find untarred directory for {chart_name}")
        return None

    return untar_dir


def main(yaml_file, target_node=None, test_mode="oob"):
    """Main function to process deployment configuration.

    Args:
        yaml_file: Path to the YAML configuration file
        target_node: Optional target number of nodes to deploy. If not specified, will process all nodes.
        test_mode: Test mode, either "oob" (out of box) or "tune". Defaults to "oob".
    """
    if test_mode not in ["oob", "tune"]:
        print("Error: test_mode must be either 'oob' or 'tune'")
        return None

    config = read_yaml(yaml_file)
    if config is None:
        print("Failed to read YAML file.")
        return None

    deploy_config = config["deploy"]
    benchmark_config = config["benchmark"]

    # Extract chart name from the YAML file name
    chart_name = os.path.splitext(os.path.basename(yaml_file))[0].split("_")[-1]
    print(f"chart_name: {chart_name}")
    python_cmd = sys.executable

    # Process nodes
    nodes = deploy_config.get("node", [])
    if not isinstance(nodes, list):
        print("Error: deploy_config['node'] must be an array")
        return None

    nodes_to_process = [target_node] if target_node is not None else nodes
    node_names = deploy_config.get("node_name", [])
    namespace = deploy_config.get("namespace", "default")

    # Pull the Helm chart
    chart_pull_url = f"oci://ghcr.io/opea-project/charts/{chart_name}"
    version = deploy_config.get("version", "0-latest")
    chart_dir = pull_helm_chart(chart_pull_url, version, chart_name)
    if not chart_dir:
        return

    for node in nodes_to_process:
        try:
            print(f"\nProcessing configuration for {node} nodes...")

            # Get corresponding node names for this node count
            current_node_names = node_names[:node] if node_names else []

            # Add labels for current node configuration
            print(f"Adding labels for {node} nodes...")
            cmd = [python_cmd, "deploy.py", "--chart-name", chart_name, "--num-nodes", str(node), "--add-label"]
            if current_node_names:
                cmd.extend(["--node-names"] + current_node_names)

            result = subprocess.run(cmd, check=True)
            if result.returncode != 0:
                print(f"Failed to add labels for {node} nodes")
                continue

            try:
                # Only process batch parameters in tune mode
                if test_mode == "tune":
                    # Process batch parameters based on engine type
                    llm_config = deploy_config.get("services", {}).get("llm", {})
                    engine = llm_config.get("engine", "tgi")

                    if engine == "tgi":
                        batch_params = llm_config.get("max_batch_size", [])
                        param_name = "max_batch_size"
                    elif engine == "vllm":
                        batch_params = llm_config.get("max_num_seqs", [])
                        param_name = "max_num_seqs"
                    else:
                        print(f"Unsupported LLM engine: {engine}")
                        continue

                    if not isinstance(batch_params, list):
                        batch_params = [batch_params]

                    # Skip multiple iterations if batch parameter is empty
                    if batch_params == [""] or not batch_params:
                        batch_params = [None]
                else:
                    # In OOB mode, just do one iteration with no batch parameter
                    batch_params = [None]
                    param_name = "batch_param"

                # Get timeout and interval from deploy config for check-ready
                timeout = deploy_config.get("timeout", 1000)  # default 1000s
                interval = deploy_config.get("interval", 5)  # default 5s

                values_file_path = None
                for i, batch_param in enumerate(batch_params):
                    if test_mode == "tune":
                        print(f"\nProcessing {param_name}: {batch_param}")
                    else:
                        print("\nProcessing OOB deployment")

                    # Construct new deploy config
                    new_deploy_config = construct_deploy_config(deploy_config, node, batch_param)

                    # Write the new deploy config to a temporary file
                    temp_config_file = (
                        f"temp_deploy_config_{node}.yaml"
                        if batch_param is None
                        else f"temp_deploy_config_{node}_{batch_param}.yaml"
                    )
                    try:
                        with open(temp_config_file, "w") as f:
                            yaml.dump(new_deploy_config, f)

                        if i == 0:
                            # First iteration: full deployment
                            cmd = [
                                python_cmd,
                                "deploy.py",
                                "--deploy-config",
                                temp_config_file,
                                "--chart-name",
                                chart_name,
                                "--namespace",
                                namespace,
                                "--chart-dir",
                                chart_dir,
                                "--test-mode",
                                test_mode,
                            ]
                            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

                            match = re.search(r"values_file_path: (\S+)", result.stdout)
                            if match:
                                values_file_path = match.group(1)
                                print(f"Captured values_file_path: {values_file_path}")
                            else:
                                print("values_file_path not found in the output")

                        else:
                            # Subsequent iterations: update services with config change
                            cmd = [
                                python_cmd,
                                "deploy.py",
                                "--deploy-config",
                                temp_config_file,
                                "--chart-name",
                                chart_name,
                                "--namespace",
                                namespace,
                                "--chart-dir",
                                chart_dir,
                                "--user-values",
                                values_file_path,
                                "--update-service",
                                "--test-mode",
                                test_mode,
                            ]
                            result = subprocess.run(cmd, check=True)
                            if result.returncode != 0:
                                print(f"Update failed for {node} nodes configuration with {param_name} {batch_param}")
                                break  # Skip remaining {param_name} for this node

                        # Wait for deployment to be ready
                        print("\nWaiting for deployment to be ready...")
                        cmd = [
                            python_cmd,
                            "deploy.py",
                            "--chart-name",
                            chart_name,
                            "--namespace",
                            namespace,
                            "--check-ready",
                            "--timeout",
                            str(timeout),
                            "--interval",
                            str(interval)
                        ]
                        try:
                            result = subprocess.run(cmd, check=True)
                            print("Deployments are ready!")
                        except subprocess.CalledProcessError as e:
                            print(f"Deployments status failed with returncode: {e.returncode}")

                        # Run benchmark
                        run_benchmark(
                            benchmark_config=benchmark_config,
                            chart_name=chart_name,
                            namespace=namespace,
                            node_num=node,
                            llm_model=deploy_config.get("services", {}).get("llm", {}).get("model_id", ""),
                        )

                    except Exception as e:
                        print(
                            f"Error during {'deployment' if i == 0 else 'update'} for {node} nodes with {param_name} {batch_param}: {str(e)}"
                        )
                        break  # Skip remaining {param_name} for this node
                    finally:
                        # Clean up the temporary file
                        if os.path.exists(temp_config_file):
                            os.remove(temp_config_file)

            finally:
                # Uninstall the deployment
                print(f"\nUninstalling deployment for {node} nodes...")
                cmd = [
                    python_cmd,
                    "deploy.py",
                    "--chart-name",
                    chart_name,
                    "--namespace",
                    namespace,
                    "--uninstall",
                ]
                try:
                    result = subprocess.run(cmd, check=True)
                    if result.returncode != 0:
                        print(f"Failed to uninstall deployment for {node} nodes")
                except Exception as e:
                    print(f"Error while uninstalling deployment for {node} nodes: {str(e)}")

                # Delete labels for current node configuration
                print(f"Deleting labels for {node} nodes...")
                cmd = [python_cmd, "deploy.py", "--chart-name", chart_name, "--num-nodes", str(node), "--delete-label"]
                if current_node_names:
                    cmd.extend(["--node-names"] + current_node_names)

                try:
                    result = subprocess.run(cmd, check=True)
                    if result.returncode != 0:
                        print(f"Failed to delete labels for {node} nodes")
                except Exception as e:
                    print(f"Error while deleting labels for {node} nodes: {str(e)}")

        except Exception as e:
            print(f"Error processing configuration for {node} nodes: {str(e)}")
            continue

    # Cleanup: Remove the untarred directory
    if chart_dir and os.path.isdir(chart_dir):
        print(f"Removing temporary directory: {chart_dir}")
        shutil.rmtree(chart_dir)
        print("Temporary directory removed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy and benchmark with specific node configuration.")
    parser.add_argument("yaml_file", help="Path to the YAML configuration file")
    parser.add_argument("--target-node", type=int, help="Optional: Target number of nodes to deploy.", default=None)
    parser.add_argument("--test-mode", type=str, help="Test mode, either 'oob' (out of box) or 'tune'.", default="oob")

    args = parser.parse_args()
    main(args.yaml_file, args.target_node, args.test_mode)
