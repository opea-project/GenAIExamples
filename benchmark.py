# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from datetime import datetime

import requests
import yaml
from evals.benchmark.stresscli.commands.load_test import locust_runtests
from kubernetes import client, config

# only support chatqna for now
service_endpoints = {
    "chatqna": "/v1/chatqna",
}


def load_yaml(file_path):
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    return data


def construct_benchmark_config(test_suite_config):
    """Extract relevant data from the YAML based on the specified test cases."""

    return {
        "user_queries": test_suite_config.get("user_queries", [1]),
        "concurrency": test_suite_config.get("concurrency", [1]),
        "load_shape_type": test_suite_config.get("load_shape_type", "constant"),
        "poisson_arrival_rate": test_suite_config.get("poisson_arrival_rate", 1.0),
        "warmup_iterations": test_suite_config.get("warmup_iterations", 10),
        "seed": test_suite_config.get("seed", None),
        "bench_target": test_suite_config.get("bench_target", ["chatqnafixed"]),
        "dataset": test_suite_config.get("dataset", ""),
        "prompt": test_suite_config.get("prompt", [10]),
        "llm_max_token_size": test_suite_config.get("llm", {}).get("max_token_size", [128]),
    }


def _get_cluster_ip(service_name, namespace="default"):
    """Get the Cluster IP of a service in a Kubernetes cluster."""
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
        namespace (str): The namespace of the service (default is "default").

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


def _create_yaml_content(service, base_url, bench_target, test_phase, num_queries, test_params, concurrency=1):
    """Create content for the run.yaml file."""

    # calculate the number of concurrent users
    concurrent_level = int(num_queries // concurrency)

    import importlib.util

    package_name = "opea-eval"
    spec = importlib.util.find_spec(package_name)
    print(spec)

    # get folder path of opea-eval
    eval_path = os.getenv("EVAL_PATH", "")
    if not eval_path:
        import pkg_resources

        for dist in pkg_resources.working_set:
            if "opea-eval" in dist.project_name:
                eval_path = dist.location
                break
    if not eval_path:
        print("Fail to find the opea-eval package. Please set/install it first.")
        exit(1)

    load_shape = test_params["load_shape"]
    load_shape["params"]["constant"] = {"concurrent_level": concurrent_level}

    yaml_content = {
        "profile": {
            "storage": {"hostpath": test_params["test_output_dir"]},
            "global-settings": {
                "tool": "locust",
                "locustfile": os.path.join(eval_path, "evals/benchmark/stresscli/locust/aistress.py"),
                "host": base_url,
                "run-time": test_params["run_time"],
                "stop-timeout": test_params["query_timeout"],
                "processes": 16,  # set to 2 by default
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
                "load-shape": load_shape,
            },
            "runs": [{"name": test_phase, "users": concurrency, "max-request": num_queries}],
        }
    }

    return yaml_content


def _create_stresscli_confs(case_params, test_params, test_phase, num_queries, base_url, ts, concurrency=1) -> str:
    """Create a stresscli configuration file and persist it on disk."""
    stresscli_confs = []
    # Get the workload
    bench_target = test_params["bench_target"]
    for i, b_target in enumerate(bench_target):
        stresscli_conf = {}
        print(f"[OPEA BENCHMARK] 🚀 Running test for {b_target} in phase {test_phase} for {num_queries} queries")
        if len(test_params["dataset"]) > i:
            stresscli_conf["envs"] = {"DATASET": test_params["dataset"][i], "MAX_LINES": str(test_params["prompt"][i])}
        else:
            stresscli_conf["envs"] = {"MAX_LINES": str(test_params["prompt"][i])}
        # Generate the content of stresscli configuration file
        stresscli_yaml = _create_yaml_content(
            case_params, base_url, b_target, test_phase, num_queries, test_params, concurrency
        )

        # Dump the stresscli configuration file
        service_name = case_params.get("service_name")
        max_output = case_params.get("max_output")
        run_yaml_path = os.path.join(
            test_params["test_output_dir"],
            f"run_{test_phase}_{service_name}_{num_queries}_{b_target}_{max_output}_{ts}.yaml",
        )
        with open(run_yaml_path, "w") as yaml_file:
            yaml.dump(stresscli_yaml, yaml_file)
        stresscli_conf["run_yaml_path"] = run_yaml_path
        stresscli_confs.append(stresscli_conf)
    return stresscli_confs


def create_stresscli_confs(service, base_url, test_suite_config, index):
    """Create and save the run.yaml file for the service being tested."""
    os.makedirs(test_suite_config["test_output_dir"], exist_ok=True)

    stresscli_confs = []

    # Add YAML configuration of stresscli for warm-ups
    warm_ups = test_suite_config["warm_ups"]
    if warm_ups is not None and warm_ups > 0:
        stresscli_confs.extend(_create_stresscli_confs(service, test_suite_config, "warmup", warm_ups, base_url, index))

    # Add YAML configuration of stresscli for benchmark
    user_queries_lst = test_suite_config["user_queries"]
    if user_queries_lst is None or len(user_queries_lst) == 0:
        # Test stop is controlled by run time
        stresscli_confs.extend(_create_stresscli_confs(service, test_suite_config, "benchmark", -1, base_url, index))
    else:
        # Test stop is controlled by request count
        for i, user_query in enumerate(user_queries_lst):
            concurrency_list = test_suite_config["concurrency"]
            user_query *= test_suite_config["node_num"]
            stresscli_confs.extend(
                _create_stresscli_confs(
                    service,
                    test_suite_config,
                    "benchmark",
                    user_query,
                    base_url,
                    index,
                    concurrency=concurrency_list[i],
                )
            )

    return stresscli_confs


def ingest_data_to_db(service, dataset, namespace):
    """Ingest data into the database."""
    for service_name in service.get("service_list"):
        if "data" in service_name:
            # Ingest data into the database
            print(f"[OPEA BENCHMARK] 🚀 Ingesting data into the database for {service_name}...")
            try:
                svc_ip, port = _get_service_ip(service_name, "k8s", None, None, namespace)
                url = f"http://{svc_ip}:{port}/v1/dataprep/ingest"

                files = {"files": open(dataset, "rb")}

                response = requests.post(url, files=files)
                if response.status_code != 200:
                    print(f"Error ingesting data: {response.text}. Status code: {response.status_code}")
                    return False
                if "Data preparation succeeded" not in response.text:
                    print(f"Error ingesting data: {response.text}. Response: {response}")
                    return False

            except Exception as e:
                print(f"Error ingesting data: {e}")
                return False
            print(f"[OPEA BENCHMARK] 🚀 Data ingestion completed for {service_name}.")
            break
    return True


def clear_db(service, namespace):
    """Delete all files from the database."""
    for service_name in service.get("service_list"):
        if "data" in service_name:
            # Delete data from the database
            try:
                svc_ip, port = _get_service_ip(service_name, "k8s", None, None, namespace)
                url = f"http://{svc_ip}:{port}/v1/dataprep/delete"
                data = {"file_path": "all"}
                print(f"[OPEA BENCHMARK] 🚀 Deleting data from the database for {service_name} with {url}")

                response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
                if response.status_code != 200:
                    print(f"Error deleting data: {response.text}. Status code: {response.status_code}")
                    return False
                if "true" not in response.text:
                    print(f"Error deleting data: {response.text}. Response: {response}")
                    return False
            except Exception as e:
                print(f"Error deleting data: {e}")
                return False
            print(f"[OPEA BENCHMARK] 🚀 Data deletion completed for {service_name}.")
            break
    return True


def _run_service_test(example, service, test_suite_config, namespace):
    """Run the test for a specific service and example."""
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

    base_url = f"http://{svc_ip}:{port}"
    endpoint = service_endpoints[example]
    url = f"{base_url}{endpoint}"
    print(f"[OPEA BENCHMARK] 🚀 Running test for {service_name} at {url}")

    # Generate a unique index based on the current time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the run.yaml for the service
    stresscli_confs = create_stresscli_confs(service, base_url, test_suite_config, timestamp)

    # Do benchmark in for-loop for different user queries
    output_folders = []
    for index, stresscli_conf in enumerate(stresscli_confs, start=1):
        run_yaml_path = stresscli_conf["run_yaml_path"]
        print(f"[OPEA BENCHMARK] 🚀 The {index} time test is running, run yaml: {run_yaml_path}...")
        os.environ["MAX_TOKENS"] = str(service.get("max_output"))

        dataset = None
        if stresscli_conf.get("envs") is not None:
            for key, value in stresscli_conf.get("envs").items():
                os.environ[key] = value
                if key == "DATASET":
                    dataset = value

        if dataset:
            # Ingest data into the database for single run of benchmark
            result = ingest_data_to_db(service, dataset, namespace)
            if not result:
                print(f"[OPEA BENCHMARK] 🚀 Data ingestion failed for {service_name}.")
                exit(1)
        else:
            print(f"[OPEA BENCHMARK] 🚀 Dataset is not specified for {service_name}. Check the benchmark.yaml again.")

        # Run the benchmark test and append the output folder to the list
        print("[OPEA BENCHMARK] 🚀 Start locust_runtests at", datetime.now().strftime("%Y%m%d_%H%M%S"))
        locust_output = locust_runtests(None, run_yaml_path)
        print(f"[OPEA BENCHMARK] 🚀 locust_output origin name is {locust_output}")
        # Rename the output folder to include the index
        new_output_path = os.path.join(
            os.path.dirname(run_yaml_path), f"{os.path.splitext(os.path.basename(run_yaml_path))[0]}_output"
        )
        os.rename(locust_output, new_output_path)
        print(f"[OPEA BENCHMARK] 🚀 locust new_output_path is {new_output_path}")

        output_folders.append(new_output_path)
        print("[OPEA BENCHMARK] 🚀 End locust_runtests at", datetime.now().strftime("%Y%m%d_%H%M%S"))

        # Delete all files from the database after the test
        result = clear_db(service, namespace)
        print("[OPEA BENCHMARK] 🚀 End of clean up db", datetime.now().strftime("%Y%m%d_%H%M%S"))
        if not result:
            print(f"[OPEA BENCHMARK] 🚀 Data deletion failed for {service_name}.")
            exit(1)

    print(f"[OPEA BENCHMARK] 🚀 Test completed for {service_name} at {url}")
    return output_folders


def run_benchmark(benchmark_config, chart_name, namespace, node_num=1, llm_model=None, report=False, output_dir=None):
    """Run the benchmark test for the specified helm chart and configuration.

    Args:
        benchmark_config (dict): The benchmark configuration.
        chart_name (str): The name of the helm chart.
        namespace (str): The namespace to deploy the chart.
        node_num (int): The number of nodes of current deployment.
        llm_model (str): The LLM model to use for the test.
        report (bool): Whether to generate a report after the test.
        output_dir (str): Directory to store the test output. If None, uses default directory.
    """
    # If llm_model is None or an empty string, set to default value
    if not llm_model:
        llm_model = "meta-llama/Meta-Llama-3-8B-Instruct"

    # Extract data
    parsed_data = construct_benchmark_config(benchmark_config)
    test_suite_config = {
        "user_queries": parsed_data["user_queries"],  # num of user queries
        "random_prompt": False,  # whether to use random prompt, set to False by default
        "run_time": "30m",  # The max total run time for the test suite, set to 60m by default
        "collect_service_metric": False,  # whether to collect service metrics, set to False by default
        "llm_model": llm_model,  # The LLM model used for the test
        "deployment_type": "k8s",  # Default is "k8s", can also be "docker"
        "service_ip": None,  # Leave as None for k8s, specify for Docker
        "service_port": None,  # Leave as None for k8s, specify for Docker
        "test_output_dir": (
            output_dir if output_dir else os.getcwd() + "/benchmark_output"
        ),  # Use output_dir if provided
        "node_num": node_num,
        "load_shape": {
            "name": parsed_data["load_shape_type"],
            "params": {
                "poisson": {"arrival_rate": parsed_data["poisson_arrival_rate"]},
            },
        },
        "concurrency": parsed_data["concurrency"],
        "arrival_rate": parsed_data["poisson_arrival_rate"],
        "query_timeout": 120,
        "warm_ups": parsed_data["warmup_iterations"],
        "seed": parsed_data["seed"],
        "namespace": namespace,
        "bench_target": parsed_data["bench_target"],
        "dataset": parsed_data["dataset"],
        "prompt": parsed_data["prompt"],
        "llm_max_token_size": parsed_data["llm_max_token_size"],
    }

    dataset = None
    query_data = None

    # Do benchmark in for-loop for different llm_max_token_size
    for llm_max_token in parsed_data["llm_max_token_size"]:
        print(f"[OPEA BENCHMARK] 🚀 Run benchmark on {dataset} with llm max-output-token {llm_max_token}.")
        case_data = {}
        # Support chatqna only for now
        if chart_name == "chatqna":
            case_data = {
                "run_test": True,
                "service_name": "chatqna",
                "service_list": [
                    "chatqna",
                    "chatqna-chatqna-ui",
                    "chatqna-data-prep",
                    "chatqna-nginx",
                    "chatqna-redis-vector-db",
                    "chatqna-retriever-usvc",
                    "chatqna-tei",
                    "chatqna-teirerank",
                    "chatqna-vllm",
                ],
                # Activate if random_prompt=true: leave blank = default dataset(WebQuestions) or sharegpt
                "prompts": query_data,
                "max_output": llm_max_token,  # max number of output tokens
                "k": 1,  # number of retrieved documents
            }
        output_folder = _run_service_test(chart_name, case_data, test_suite_config, namespace)

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


if __name__ == "__main__":
    benchmark_config = load_yaml("./ChatQnA/benchmark_chatqna.yaml")
    run_benchmark(benchmark_config=benchmark_config, chart_name="chatqna", namespace="benchmark")
