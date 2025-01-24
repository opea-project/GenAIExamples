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


def construct_deploy_config(deploy_config, target_node, max_batch_size=None):
    """Construct a new deploy config based on the target node number and optional max_batch_size.

    Args:
        deploy_config: Original deploy config dictionary
        target_node: Target node number to match in the node array
        max_batch_size: Optional specific max_batch_size value to use

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

    # Update instance_num for each service based on the same index
    for service_name, service_config in new_config.get("services", {}).items():
        if "replicaCount" in service_config:
            instance_nums = service_config["replicaCount"]
            if isinstance(instance_nums, list):
                if len(instance_nums) != len(nodes):
                    raise ValueError(
                        f"instance_num array length ({len(instance_nums)}) for service {service_name} "
                        f"doesn't match node array length ({len(nodes)})"
                    )
                service_config["replicaCount"] = instance_nums[node_index]

    # Update max_batch_size if specified
    if max_batch_size is not None and "llm" in new_config["services"]:
        new_config["services"]["llm"]["max_batch_size"] = max_batch_size

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


def main(yaml_file, target_node=None):
    """Main function to process deployment configuration.

    Args:
        yaml_file: Path to the YAML configuration file
        target_node: Optional target number of nodes to deploy. If not specified, will process all nodes.
    """
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
    version = deploy_config.get("version", "1.1.0")
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
                # Process max_batch_sizes
                max_batch_sizes = deploy_config.get("services", {}).get("llm", {}).get("max_batch_size", [])
                if not isinstance(max_batch_sizes, list):
                    max_batch_sizes = [max_batch_sizes]

                values_file_path = None
                for i, max_batch_size in enumerate(max_batch_sizes):
                    print(f"\nProcessing max_batch_size: {max_batch_size}")

                    # Construct new deploy config
                    new_deploy_config = construct_deploy_config(deploy_config, node, max_batch_size)

                    # Write the new deploy config to a temporary file
                    temp_config_file = f"temp_deploy_config_{node}_{max_batch_size}.yaml"
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
                            ]
                            result = subprocess.run(cmd, check=True)
                            if result.returncode != 0:
                                print(
                                    f"Update failed for {node} nodes configuration with max_batch_size {max_batch_size}"
                                )
                                break  # Skip remaining max_batch_sizes for this node

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
                            llm_model=deploy_config.get("services", {}).get("llm", {}).get("model_id", ""),
                        )

                    except Exception as e:
                        print(
                            f"Error during {'deployment' if i == 0 else 'update'} for {node} nodes with max_batch_size {max_batch_size}: {str(e)}"
                        )
                        break  # Skip remaining max_batch_sizes for this node
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

    args = parser.parse_args()
    main(args.yaml_file, args.target_node)
