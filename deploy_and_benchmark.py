# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
 
import os
import re
import sys
import yaml
import copy
import json
import time
import shutil
import argparse
import subprocess
from datetime import datetime

eval_path = '/home/sdp/letong/GenAIEval/'
sys.path.append(eval_path)
from evals.benchmark.stresscli.commands.load_test import locust_runtests
from kubernetes import client, config


############################################
#               load yaml                  #
############################################
service_endpoints = {
    "chatqna": "/v1/chatqna",
    "codegen": "/v1/codegen",
    "codetrans": "/v1/codetrans",
    "faqgen": "/v1/faqgen",
    "audioqna": "/v1/audioqna",
    "visualqna": "/v1/visualqna",
}


def load_yaml(file_path):
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None


def construct_benchmark_config(content):
    """Extract relevant data from the YAML based on the specified test cases."""
    # Extract test suite configuration
    test_suite_config = content.get("benchmark", {})
 
    return {
        # no examples param
        "example_name": test_suite_config.get("example_name", "chatqna"),
        "concurrency": test_suite_config.get("concurrency", []),
        "totoal_query_num": test_suite_config.get("user_queries", []),
        "duration:": test_suite_config.get("duration:", []),
        "query_num_per_concurrency": test_suite_config.get("query_num_per_concurrency", []),
        "possion": test_suite_config.get("possion", False),
        "possion_arrival_rate": test_suite_config.get("possion_arrival_rate", 1.0),
        "warmup_iterations": test_suite_config.get("warmup_iterations", 10),
        "seed": test_suite_config.get("seed", None),
        "dataset": test_suite_config.get("dataset", []),
        "user_query": test_suite_config.get("user_query", []),
        "query_token_size": test_suite_config.get("query_token_size"),
        "data_ratio": test_suite_config.get("data_ratio", []),
        # new params
        "dataprep_chunk_size": test_suite_config.get("data_prep", {}).get("chunk_size", [1024]),
        "dataprep_chunk_overlap": test_suite_config.get("data_prep", {}).get("chunk_overlap", [1000]),
        "retriever_algo": test_suite_config.get("retriever", {}).get("algo", 'IVF'),
        "retriever_fetch_k": test_suite_config.get("retriever", {}).get("fetch_k", 2),
        "rerank_top_n": test_suite_config.get("teirerank", {}).get("top_n", 2),
        "llm_max_token_size": test_suite_config.get("llm", {}).get("max_token_size", 1024),
    }


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
        if "instance_num" in service_config:
            instance_nums = service_config["instance_num"]
            if isinstance(instance_nums, list):
                if len(instance_nums) != len(nodes):
                    raise ValueError(
                        f"instance_num array length ({len(instance_nums)}) for service {service_name} "
                        f"doesn't match node array length ({len(nodes)})"
                    )
                service_config["instance_num"] = instance_nums[node_index]

    # Update max_batch_size if specified
    if max_batch_size is not None and "llm" in new_config["services"]:
        new_config["services"]["llm"]["max_batch_size"] = max_batch_size

    return new_config


############################################
#               create yaml                #
############################################
def _create_yaml_content(service, base_url, bench_target, test_phase, num_queries, test_params):
    """Create content for the run.yaml file."""
 
    # If a load shape includes the parameter concurrent_level,
    # the parameter will be passed to Locust to launch fixed
    # number of simulated users.
    concurrency = 1
    if num_queries >= 0:
        concurrency = max(1, num_queries // test_params["concurrent_level"])
    else:
        concurrency = test_params["concurrent_level"]
 
    yaml_content = {
        "profile": {
            "storage": {"hostpath": test_params["test_output_dir"]},
            "global-settings": {
                "tool": "locust",
                "locustfile": os.path.join(eval_path, "evals/benchmark/stresscli/locust/aistress.py"),
                "host": base_url,
                "stop-timeout": test_params["query_timeout"],
                "processes": 2,
                "namespace": test_params["namespace"],
                "bench-target": bench_target,
                "service-metric-collect": test_params["collect_service_metric"],
                "service-list": service.get("service_list", []),
                "dataset": service.get("dataset", "default"),
                "prompts": service.get("prompts", None),
                "max-output": service.get("max_output", 128),
                "seed": test_params.get("seed", None),
                "llm-model": test_params["llm_model"],
                "deployment-type": test_params["deployment_type"],
            },
            "runs": [{"name": test_phase, "users": concurrency, "max-request": num_queries}],
        }
    }
 
    # For the following scenarios, test will stop after the specified run-time
    # 1) run_time is not specified in benchmark.yaml
    # 2) Not a warm-up run
    # TODO: According to Locust's doc, run-time should default to run forever,
    # however the default is 48 hours.
    if test_params["run_time"] is not None and test_phase != "warmup":
        yaml_content["profile"]["global-settings"]["run-time"] = test_params["run_time"]
 
    return yaml_content
 
 
def _create_stresscli_yaml(
    example, case_type, case_params, test_params, test_phase, num_queries, base_url, ts
) -> str:
    """Create a stresscli configuration file and persist it on disk.
 
    Parameters
    ----------
        example : str
            The name of the example.
        case_type : str
            The type of the test case
        case_params : dict
            The parameters of single test case.
        test_phase : str [warmup|benchmark]
            Current phase of the test.
        num_queries : int
            The number of test requests sent to SUT
        base_url : str
            The root endpoint of SUT
        test_params : dict
            The parameters of the test
        ts : str
            Timestamp
 
    Returns
    -------
        run_yaml_path : str
            The path of the generated YAML file.
    """
    # Get the workload
    dataset = test_params["dataset"]
    if "pub_med" in dataset:
        bench_target = "chatqna_qlist_pubmed"
        max_lines = dataset.split("pub_med")[-1]
        os.environ['DATASET'] = f"pubmed_{max_lines}.txt"
        os.environ['MAX_LINES'] = max_lines
        print("================ max_lines ==================")
        print(max_lines)
        print("-----------------------------------------------")

    # Generate the content of stresscli configuration file
    stresscli_yaml = _create_yaml_content(case_params, base_url, bench_target, test_phase, num_queries, test_params)
 
    # Dump the stresscli configuration file
    service_name = case_params.get("service_name")
    run_yaml_path = os.path.join(
        test_params["test_output_dir"], f"run_{service_name}_{ts}_{test_phase}_{num_queries}.yaml"
    )
    with open(run_yaml_path, "w") as yaml_file:
        yaml.dump(stresscli_yaml, yaml_file)
 
    return run_yaml_path
 
 
def create_benchmark_yaml(example, deployment_type, service_type, service, base_url, test_suite_config, index):
    """Create and save the run.yaml file for the service being tested."""
    os.makedirs(test_suite_config["test_output_dir"], exist_ok=True)

    run_yaml_paths = []
 
    # Add YAML configuration of stresscli for warm-ups
    warm_ups = test_suite_config["warm_ups"]
    if warm_ups is not None and warm_ups > 0:
        run_yaml_paths.append(
            _create_stresscli_yaml(
                example, service_type, service, test_suite_config, "warmup", warm_ups, base_url, index
            )
        )

    # Add YAML configuration of stresscli for benchmark
    user_queries_lst = test_suite_config["user_queries"]
    if user_queries_lst is None or len(user_queries_lst) == 0:
        # Test stop is controlled by run time
        run_yaml_paths.append(
            _create_stresscli_yaml(
                example, service_type, service, test_suite_config, "benchmark", -1, base_url, index
            )
        )
    else:
        # Test stop is controlled by request count
        for user_queries in user_queries_lst:
            run_yaml_paths.append(
                _create_stresscli_yaml(
                    example, service_type, service, test_suite_config, "benchmark", user_queries, base_url, index
                )
            )
 
    return run_yaml_paths


############################################
#                benchmark                 #
############################################
def _get_cluster_ip(service_name, namespace="default"):
    # Load the Kubernetes configuration
    config.load_kube_config()  # or use config.load_incluster_config() if running inside a Kubernetes pod
 
    # Create an API client for the core API (which handles services)
    v1 = client.CoreV1Api()
 
    try:
        # Get the service object
        service = v1.read_namespaced_service(name=service_name, namespace=namespace)
 
        # Extract the Cluster IP
        cluster_ip = service.spec.cluster_ip
 
        # Extract the port number (assuming the first port, modify if necessary)
        if service.spec.ports:
            port_number = service.spec.ports[0].port  # Get the first port number
        else:
            port_number = None
 
        return cluster_ip, port_number
    except client.exceptions.ApiException as e:
        print(f"Error fetching service: {e}")
        return None


def _get_service_ip(service_name, deployment_type="k8s", service_ip=None, service_port=None, namespace="default"):
    """Get the service IP and port based on the deployment type.
 
    Args:
        service_name (str): The name of the service.
        deployment_type (str): The type of deployment ("k8s" or "docker").
        service_ip (str): The IP address of the service (required for Docker deployment).
        service_port (int): The port of the service (required for Docker deployment).
 
    Returns:
        (str, int): The service IP and port.
    """
    if deployment_type == "k8s":
        # Kubernetes IP and port retrieval logic
        svc_ip, port = _get_cluster_ip(service_name, namespace)
    elif deployment_type == "docker":
        # For Docker deployment, service_ip and service_port must be specified
        if not service_ip or not service_port:
            raise ValueError(
                "For Docker deployment, service_ip and service_port must be provided in the configuration."
            )
        svc_ip = service_ip
        port = service_port
    else:
        raise ValueError("Unsupported deployment type. Use 'k8s' or 'docker'.")
 
    return svc_ip, port


def _run_service_test(example, service_type, service, test_suite_config):
    print(f"[OPEA BENCHMARK] 🚀 Example: [ {example} ] Service: [ {service.get('service_name')} ], Running test...")
    
    # Get the service name
    service_name = service.get("service_name")
 
    # Get the deployment type from the test suite configuration
    deployment_type = test_suite_config.get("deployment_type", "k8s")
 
    # Get the service IP and port based on deployment type
    svc_ip, port = _get_service_ip(
        service_name,
        deployment_type,
        test_suite_config.get("service_ip"),
        test_suite_config.get("service_port"),
        test_suite_config.get("namespace"),
    )
    # svc_ip, port = "localhost", "8888"

    print("=============== svc_ip, port ==================")
    print(svc_ip)
    print(port)
    print("-----------------------------------------------")
 
    base_url = f"http://{svc_ip}:{port}"
    endpoint = service_endpoints[example]
    url = f"{base_url}{endpoint}"
    print(f"[OPEA BENCHMARK] 🚀 Running test for {service_name} at {url}")
 
    # Generate a unique index based on the current time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
 
    # Create the run.yaml for the service
    run_yaml_paths = create_benchmark_yaml(
        example, deployment_type, service_type, service, base_url, test_suite_config, timestamp
    )

    print("============== run_yaml_paths =================")
    print(run_yaml_paths)
    print("-----------------------------------------------")

    # Run the test using locust_runtests function
    output_folders = []
    for index, run_yaml_path in enumerate(run_yaml_paths, start=1):
        print(f"[OPEA BENCHMARK] 🚀 The {index} time test is running, run yaml: {run_yaml_path}...")
        output_folders.append(locust_runtests(None, run_yaml_path))
 
    print(f"[OPEA BENCHMARK] 🚀 Test completed for {service_name} at {url}")
 
    return output_folders


def run_benchmark(benchmark_config, report=False):
    # Extract data
    parsed_data = construct_benchmark_config(benchmark_config)
    os.environ['MAX_TOKENS'] = str(parsed_data['llm_max_token_size'])
    print("================ parsed data ==================")
    print(parsed_data)
    print("-----------------------------------------------")
    test_suite_config = {
        "user_queries": [1,2,4],  # num of user queries set to 1 by default
        "random_prompt": False, # whether to use random prompt, set to False by default
        "run_time": "60m", # The max total run time for the test suite, set to 60m by default
        "collect_service_metric": False, # whether to collect service metrics, set to False by default
        "llm_model": "Qwen/Qwen2.5-Coder-7B-Instruct", # The LLM model used for the test
        "deployment_type": "k8s", # Default is "k8s", can also be "docker"
        "service_ip": None, # Leave as None for k8s, specify for Docker
        "service_port": None, # Leave as None for k8s, specify for Docker
        "test_output_dir": "/home/sdp/letong/GenAIExamples/benchmark_output", # The directory to store the test output
        "load_shape": {"name":"constant", "params":{"constant":{"concurrent_level": 4},"poisson":{"arrival_rate":1.0}}},
        "concurrent_level": 4,
        "arrival_rate": 1.0,
        "query_timeout": 120,
        "warm_ups": 0,
        "seed": None,
        "namespace": "default",
        "dataset": parsed_data["dataset"],
        "data_ratio": parsed_data["data_ratio"]
    }
    print("============= test_suite_config ===============")
    print(test_suite_config)
    print("-----------------------------------------------")

    service_type="e2e"
    dataset = None
    query_data = None
    case_data = {
        "run_test": True,
        "service_name": "chatqna-backend-server-svc",
        "service_list": [
            "chatqna-backend-server-svc",
            "embedding-dependency-svc",
            "embedding-svc",
            "llm-dependency-svc",
            "llm-svc",
            "retriever-svc",
            "vector-db"
        ],
        "dataset": dataset, # Activate if random_prompt=true: leave blank = default dataset(WebQuestions) or sharegpt
        "prompts": query_data,
        "max_output": 128,  # max number of output tokens
        "k": 1 # number of retrieved documents
    }
    print("================= case_data ===================")
    print(case_data)
    print("-----------------------------------------------")
    output_folder = _run_service_test(parsed_data["example_name"], service_type, case_data, test_suite_config)
    print(f"[OPEA BENCHMARK] 🚀 Test Finished. Output saved in {output_folder}.")

    if report:
        print(output_folder)
        all_results = dict()
        for folder in output_folder:
            from evals.benchmark.stresscli.commands.report import get_report_results

            results = get_report_results(folder)
            all_results[folder] = results
            print(f"results = {results}\n")
 
        return all_results


############################################
#                deployment                #
############################################
def deploy_pull_helm_chart(chart_pull_url, version, chart_name):
    # Pull and untar the chart
    subprocess.run(["helm", "pull", chart_pull_url, "--version", version, "--untar"], check=True)

    current_dir = os.getcwd()
    untar_dir = os.path.join(current_dir, chart_name)

    if not os.path.isdir(untar_dir):
        print(f"Error: Could not find untarred directory for {chart_name}")
        return None

    return untar_dir


def _run_kubectl_command(command):
    """Run a kubectl command and return the output."""
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\n{e.stderr}")
        exit(1)


def _get_all_nodes():
    """Get the list of all nodes in the Kubernetes cluster."""
    command = ["kubectl", "get", "nodes", "-o", "json"]
    output = _run_kubectl_command(command)
    nodes = json.loads(output)
    return [node["metadata"]["name"] for node in nodes["items"]]


def _add_label_to_node(node_name, label):
    """Add a label to the specified node."""
    command = ["kubectl", "label", "node", node_name, label, "--overwrite"]
    print(f"Labeling node {node_name} with {label}...")
    _run_kubectl_command(command)
    print(f"Label {label} added to node {node_name} successfully.")


def deploy_add_labels(label, num_nodes, node_names=None):
    """Add a label to the specified number of nodes or to specified nodes."""

    print(f"Adding labels for {num_nodes} nodes...")
    try:
        if node_names:
            # Add label to the specified nodes
            for node_name in node_names:
                _add_label_to_node(node_name, label)
        else:
            # Fetch the node list and label the specified number of nodes
            all_nodes = _get_all_nodes()
            if num_nodes is None or num_nodes > len(all_nodes):
                print(f"Error: Node count exceeds the number of available nodes ({len(all_nodes)} available).")
                return False

            selected_nodes = all_nodes[:num_nodes]
            for node_name in selected_nodes:
                _add_label_to_node(node_name, label)
        return True
    except Exception as e:
        print(f"Fail to add label {label} for nodes.")
        return False


def deploy_delete_labels(label, node_names=None):
    """Clear the specified label from specific nodes if provided, otherwise from all nodes."""
    label_key = label.split("=")[0]  # Extract key from 'key=value' format

    # If specific nodes are provided, use them; otherwise, get all nodes
    nodes_to_clear = node_names if node_names else _get_all_nodes()

    for node_name in nodes_to_clear:
        # Check if the node has the label by inspecting its metadata
        command = ["kubectl", "get", "node", node_name, "-o", "json"]
        node_info = _run_kubectl_command(command)
        node_metadata = json.loads(node_info)

        # Check if the label exists on this node
        labels = node_metadata["metadata"].get("labels", {})
        if label_key in labels:
            # Remove the label from the node
            command = ["kubectl", "label", "node", node_name, f"{label_key}-"]
            print(f"Removing label {label_key} from node {node_name}...")
            _run_kubectl_command(command)
            print(f"Label {label_key} removed from node {node_name} successfully.")
        else:
            print(f"Label {label_key} not found on node {node_name}, skipping.")


def _read_deploy_config(config_path):
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


def _get_hw_values_file(deploy_config, chart_dir):
    """Get the hardware-specific values file based on the deploy configuration."""
    device_type = deploy_config.get("device", "cpu")
    print(f"Device type is {device_type}. Using existing Helm chart values files...")

    if device_type == "cpu":
        return None

    llm_engine = deploy_config.get("services", {}).get("llm", {}).get("engine", "tgi")
    version = deploy_config.get("version", "1.1.0")

    if not os.path.isdir(chart_dir):
        print(f"Error: Directory not found - {chart_dir}")
        return None

    hw_values_file = (
        os.path.join(chart_dir, f"{device_type}-values.yaml")
        if version in ["1.0.0", "1.1.0"]
        else os.path.join(chart_dir, f"{device_type}-{llm_engine}-values.yaml")
    )

    if os.path.exists(hw_values_file):
        print(f"Device-specific values file found: {hw_values_file}")
        return hw_values_file

    print(f"Warning: {hw_values_file} not found")
    return None


def _configure_node_selectors(values, node_selector, deploy_config):
    """Configure node selectors for all services."""
    for service_name, service_config in deploy_config["services"].items():
        if service_name == "backend":
            values["nodeSelector"] = {key: value for key, value in node_selector.items()}
        elif service_name == "llm":
            engine = service_config.get("engine", "tgi")
            values[engine] = {"nodeSelector": {key: value for key, value in node_selector.items()}}
        else:
            values[service_name] = {"nodeSelector": {key: value for key, value in node_selector.items()}}
    return values


def _configure_replica(values, deploy_config):
    """Get replica configuration based on example type and node count."""
    for service_name, service_config in deploy_config["services"].items():
        if not service_config.get("instance_num"):
            continue

        if service_name == "llm":
            engine = service_config.get("engine", "tgi")
            values[engine]["replicaCount"] = service_config["instance_num"]
        elif service_name == "backend":
            values["replicaCount"] = service_config["instance_num"]
        else:
            values[service_name]["replicaCount"] = service_config["instance_num"]

    return values


def _get_output_filename(num_nodes, with_rerank, example_type, device, action_type):
    """Generate output filename based on configuration."""
    rerank_suffix = "with-rerank-" if with_rerank else ""
    action_suffix = "deploy-" if action_type == 0 else "update-" if action_type == 1 else ""

    return f"{example_type}-{num_nodes}-{device}-{action_suffix}{rerank_suffix}values.yaml"


def _configure_resources(values, deploy_config):
    """Configure resources when tuning is enabled."""
    resource_configs = []

    for service_name, service_config in deploy_config["services"].items():
        resources = {}
        if deploy_config["device"] == "gaudi" and service_config.get("cards_per_instance", 0) > 1:
            resources = {
                "limits": {"habana.ai/gaudi": service_config["cards_per_instance"]},
                "requests": {"habana.ai/gaudi": service_config["cards_per_instance"]},
            }
        else:
            limits = {}
            requests = {}

            # Only add CPU if cores_per_instance has a value
            if service_config.get("cores_per_instance"):
                limits["cpu"] = service_config["cores_per_instance"]
                requests["cpu"] = service_config["cores_per_instance"]

            # Only add memory if memory_capacity has a value
            if service_config.get("memory_capacity"):
                limits["memory"] = service_config["memory_capacity"]
                requests["memory"] = service_config["memory_capacity"]

            # Only create resources if we have any limits/requests
            if limits and requests:
                resources["limits"] = limits
                resources["requests"] = requests

        if resources:
            if service_name == "llm":
                engine = service_config.get("engine", "tgi")
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

    for service_config in [r for r in resource_configs if r]:
        service_name = service_config["name"]
        if service_name == "backend":
            values["resources"] = service_config["resources"]
        elif service_name in values:
            values[service_name]["resources"] = service_config["resources"]

    return values


def _configure_extra_cmd_args(values, deploy_config):
    """Configure extra command line arguments for services."""
    for service_name, service_config in deploy_config["services"].items():
        extra_cmd_args = []

        for param in [
            "max_batch_size",
            "max_input_length",
            "max_total_tokens",
            "max_batch_total_tokens",
            "max_batch_prefill_tokens",
        ]:
            if service_config.get(param):
                extra_cmd_args.extend([f"--{param.replace('_', '-')}", str(service_config[param])])

        if extra_cmd_args:
            if service_name == "llm":
                engine = service_config.get("engine", "tgi")
                if engine not in values:
                    values[engine] = {}
                values[engine]["extraCmdArgs"] = extra_cmd_args
            else:
                if service_name not in values:
                    values[service_name] = {}
                values[service_name]["extraCmdArgs"] = extra_cmd_args

    return values


def _configure_models(values, deploy_config):
    """Configure model settings for services."""
    for service_name, service_config in deploy_config["services"].items():
        # Skip if no model_id defined or service is disabled
        if not service_config.get("model_id") or service_config.get("enabled") is False:
            continue

        if service_name == "llm":
            # For LLM service, use its engine as the key
            engine = service_config.get("engine", "tgi")
            values[engine]["LLM_MODEL_ID"] = service_config.get("model_id")
        elif service_name == "tei":
            values[service_name]["EMBEDDING_MODEL_ID"] = service_config.get("model_id")
        elif service_name == "teirerank":
            values[service_name]["RERANK_MODEL_ID"] = service_config.get("model_id")

    return values


def _configure_rerank(values, with_rerank, deploy_config, example_type, node_selector):
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


def _generate_helm_values(example_type, deploy_config, chart_dir, action_type, node_selector=None):
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
    values = _configure_node_selectors(values, node_selector or {}, deploy_config)
    values = _configure_rerank(values, with_rerank, deploy_config, example_type, node_selector)
    values = _configure_replica(values, deploy_config)
    values = _configure_resources(values, deploy_config)
    values = _configure_extra_cmd_args(values, deploy_config)
    values = _configure_models(values, deploy_config)

    device = deploy_config.get("device", "unknown")

    # Generate and write YAML file
    filename = _get_output_filename(num_nodes, with_rerank, example_type, device, action_type)
    yaml_string = yaml.dump(values, default_flow_style=False)

    filepath = os.path.join(chart_dir, filename)

    # Write the YAML data to the file
    with open(filepath, "w") as file:
        file.write(yaml_string)

    print(f"YAML file {filepath} has been generated.")
    return {"status": "success", "filepath": filepath}


def _update_service(release_name, chart_name, namespace, hw_values_file, deploy_values_file, update_values_file):
    """Update the deployment using helm upgrade with new values.
    """

    # Construct helm upgrade command
    command = ["helm", "upgrade", release_name, chart_name, "--namespace", namespace,
        "-f", hw_values_file, "-f", deploy_values_file, "-f", update_values_file]
    # Execute helm upgrade
    print(f"Running command: {' '.join(command)}")
    _run_kubectl_command(command)
    print("Deployment updated successfully")


def _start_service(release_name, chart_name, namespace, hw_values_file, deploy_values_file):
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


def deploy_start_services(config_file, chart_name, namespace, label, chart_dir, user_values, update_service=False):
    deploy_config = _read_deploy_config(config_file)
    if deploy_config is None:
        print("Failed to load deploy config")
        return False
    hw_values_file = _get_hw_values_file(deploy_config, chart_dir)
    node_selector = {label.split("=")[0]: label.split("=")[1]}

    # Generate values file for deploy or update service
    result = _generate_helm_values(
        example_type=chart_name,
        deploy_config=deploy_config,
        chart_dir=chart_dir,
        action_type=1 if update_service else 0,  # 0 - deploy, 1 - update
        node_selector=node_selector,
    )
    # Check result status
    if result["status"] == "success":
        values_file_path = result["filepath"]
    else:
        print(f"Failed to generate values.yaml: {result['message']}")
        return False
    
    print("start to read the generated values file")
    # Read back the generated YAML file for verification
    with open(values_file_path, "r") as file:
        print("Generated YAML contents:")
        print(file.read())
    
    # Handle service update if specified
    if update_service:
        if not user_values:
            print("user_values is required for update reference")

        try:
            _update_service(
                chart_name, chart_name, namespace, hw_values_file, user_values, values_file_path
            )
            return
        except Exception as e:
            print(f"Failed to update deployment: {str(e)}")
            return False
    # Deploy service if not update
    else:
        try:
            _start_service(
                chart_name, chart_name, namespace, hw_values_file, values_file_path
            )
            return
        except Exception as e:
            print(f"Failed to start deployment: {str(e)}")
            return False

    return result


def deploy_check_readiness(chart_name, namespace, timeout=300, interval=5, logfile="deployment.log"):
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
        deployments = subprocess.check_output(cmd, text=True).strip("'\n").split()
        
        with open(logfile, "a") as log:
            log.write(f"Found deployments: {', '.join(deployments)}\n")

        # Loop through each deployment to check its readiness
        for deployment in deployments:

            if not ("-" in deployment and chart_name in deployment and all(x not in deployment for x in ["ui", "nginx"])):
                continue

            instance, app = deployment.split("-", 1)
            cmd = ["kubectl", "-n", namespace, "get", "deployment", deployment, "-o", "jsonpath={.spec.replicas}"]
            desired_replicas = int(subprocess.check_output(cmd, text=True).strip())

            with open(logfile, "a") as log:
                log.write(f"Checking deployment '{deployment}' with desired replicas: {desired_replicas}\n")

            timer = 0
            while True:
                cmd = [
                    "kubectl", "-n", namespace, "get", "pods",
                    "-l", f"app.kubernetes.io/instance={instance}",
                    "-l", f"app.kubernetes.io/name={app}",
                    "--field-selector=status.phase=Running",
                    "-o", "json"
                ]
                pods = json.loads(subprocess.check_output(cmd, text=True))

                ready_pods = sum(all(c.get("ready") for c in p.get("status", {}).get("containerStatuses", [])) for p in pods["items"])
                terminating_pods = sum(1 for p in pods["items"] if p.get("metadata", {}).get("deletionTimestamp"))

                with open(logfile, "a") as log:
                    log.write(f"Ready pods: {ready_pods}, Desired replicas: {desired_replicas}, Terminating pods: {terminating_pods}\n")

                if ready_pods == desired_replicas and terminating_pods == 0:
                    with open(logfile, "a") as log:
                        log.write(f"Deployment '{deployment}' is ready.\n")
                    break

                if timer >= timeout:
                    with open(logfile, "a") as log:
                        log.write(f"Timeout for deployment '{deployment}'.\n")
                    return False

                time.sleep(interval)
                timer += interval

        return True  # Success for all deployments

    except (subprocess.CalledProcessError, json.JSONDecodeError, Exception) as e:
        with open(logfile, "a") as log:
            log.write(f"Error: {e}\n")
        return False


def deploy_stop_services(chart_name, namespace):
    """Uninstall a Helm release and clean up resources, optionally delete the namespace if not 'default'."""
    try:
        # Uninstall the Helm release
        command = ["helm", "uninstall", chart_name, "--namespace", namespace]
        print(f"Uninstalling Helm release {chart_name} in namespace {namespace}...")
        _run_kubectl_command(command)
        print(f"Helm release {chart_name} uninstalled successfully.")

        # If the namespace is specified and not 'default', delete it
        if namespace != "default":
            print(f"Deleting namespace {namespace}...")
            delete_namespace_command = ["kubectl", "delete", "namespace", namespace]
            _run_kubectl_command(delete_namespace_command)
            print(f"Namespace {namespace} deleted successfully.")
        else:
            print("Namespace is 'default', skipping deletion.")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while uninstalling Helm release or deleting namespace: {e}")


def deploy_and_benchmark(max_batch_sizes, deploy_config, node, chart_name, namespace, chart_dir, benchmark_config, label):
    values_file_path = None
    for i, max_batch_size in enumerate(max_batch_sizes):
        print(f"[OPEA DEPLOYMENT] 🚀 Processing max_batch_size: {max_batch_size}")

        # Construct new deploy config
        new_deploy_config = construct_deploy_config(deploy_config, node, max_batch_size)

        # Write the new deploy config to a temporary file
        temp_config_file = f"temp_deploy_config_{node}_{max_batch_size}.yaml"
        try:
            with open(temp_config_file, "w") as f:
                yaml.dump(new_deploy_config, f)

            if i == 0:
                # First iteration: full deployment
                res = deploy_start_services(config_file=temp_config_file, chart_name=chart_name, namespace=namespace, label=label, chart_dir=chart_dir, user_values=values_file_path)
                if res["status"] == "success":
                    values_file_path = res["filepath"]
                    print(f"Captured values_file_path: {values_file_path}")
                else:
                    print("values_file_path not found in the output")

            else:
                # Subsequent iterations: update services with config change
                res = deploy_start_services(config_file=temp_config_file, chart_name=chart_name, namespace=namespace, chart_dir=chart_dir, user_values=values_file_path, update_service=True)
                if res.returncode != 0:
                    print(
                        f"Update failed for {node} nodes configuration with max_batch_size {max_batch_size}"
                    )
                    break  # Skip remaining max_batch_sizes for this node

            # Wait for deployment to be ready
            print("[OPEA DEPLOYMENT] 🚀 Waiting for deployment to be ready...")
            res = deploy_check_readiness(chart_name=chart_name, namespace=namespace)
            if res:
                print("[OPEA DEPLOYMENT] 🚀 Deployments are ready!")
            else:
                print(f"Deployments status failed to start for {node} nodes with max_batch_size {max_batch_size}.")

            # run benchmark for current deployment
            run_benchmark(benchmark_config)

        except Exception as e:
            print(
                f"Error during {'deployment' if i == 0 else 'update'} for {node} nodes with max_batch_size {max_batch_size}: {str(e)}"
            )
            break  # Skip remaining max_batch_sizes for this node
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_config_file):
                os.remove(temp_config_file)


############################################
#                   main                   #
############################################
def main(yaml_file="./ChatQnA/chatqna.yaml", target_node=None):
    yaml_config = load_yaml(yaml_file)

    # Process configs for deployment and benchmark
    chart_name = os.path.splitext(os.path.basename(yaml_file))[0]
    deploy_config = yaml_config["deploy"]
    benchmark_config = yaml_config["benchmark"]

    # Prepare common variables
    nodes = deploy_config.get("node", [])
    if not isinstance(nodes, list):
        print("Error: deploy_config['node'] must be an array")
        return None
    nodes_to_process = [target_node] if target_node is not None else nodes
    node_names = deploy_config.get("node_name", [])
    namespace = deploy_config.get("namespace", "default")
    label = "example="+chart_name

    # Pull the Helm chart
    chart_pull_url = f"oci://ghcr.io/opea-project/charts/{chart_name}"
    version = deploy_config.get("version", "1.1.0")
    chart_dir = deploy_pull_helm_chart(chart_pull_url, version, chart_name)
    if not chart_dir:
        return
    
    # Run deploy and benchmark in for-loop with different nodes
    for node in nodes_to_process:
        print(f"[OPEA DEPLOYMENT] 🚀 Processing configuration for {node} nodes...")

        # Get corresponding node names for this node count
        current_node_names = node_names[:node] if node_names else []

        # Add labels for current node configuration
        print(f"[OPEA DEPLOYMENT] 🚀 Adding labels for {node} nodes...")
        res = deploy_add_labels(label=label, num_nodes=int(node), node_names=current_node_names)
        if not res:
            print(f"Failed to add labels for {node} nodes")
            continue

        # Deploy k8s nodes and run benchmarks
        try:
            # Process max_batch_sizes
            max_batch_sizes = deploy_config.get("services", {}).get("llm", {}).get("max_batch_size", [])
            if not isinstance(max_batch_sizes, list):
                max_batch_sizes = [max_batch_sizes]

            deploy_and_benchmark(max_batch_sizes, deploy_config, node, chart_name, namespace, chart_dir, benchmark_config, label)

        finally:
            # Uninstall the deployment
            print(f"[OPEA DEPLOYMENT] 🚀 Uninstalling deployment for {node} nodes...")
            res = deploy_stop_services(chart_name=chart_name, namespace=namespace)
            if res.returncode != 0:
                print(f"Failed to uninstall deployment for {node} nodes")

            # Delete labels for current node configuration
            print(f"[OPEA DEPLOYMENT] 🚀 Deleting labels for {node} nodes...")
            res = deploy_delete_labels(label=label, node_names=current_node_names)
            if res.returncode != 0:
                print(f"Failed to delete labels for {node} nodes")

    # Cleanup: Remove the untarred directory
    if chart_dir and os.path.isdir(chart_dir):
        print(f"Removing temporary directory: {chart_dir}")
        shutil.rmtree(chart_dir)
        print("Temporary directory removed successfully.")

 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy and benchmark with specific node configuration.")
    parser.add_argument("yaml_file", nargs="?", type=str, default="./ChatQnA/chatqna.yaml",
                        help="Path to the YAML configuration file. Defaults to './ChatQnA/chatqna.yaml'")
    parser.add_argument("--target-node", type=int, default=None,
                        help="Optional: Target number of nodes to deploy.")
    args = parser.parse_args()

    main(yaml_file=args.yaml_file, target_node=args.target_node)
 