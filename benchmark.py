# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from datetime import datetime

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
        "concurrency": test_suite_config.get("concurrency", []),
        "totoal_query_num": test_suite_config.get("user_queries", []),
        "duration:": test_suite_config.get("duration:", []),
        "query_num_per_concurrency": test_suite_config.get("query_num_per_concurrency", []),
        "possion": test_suite_config.get("possion", False),
        "possion_arrival_rate": test_suite_config.get("possion_arrival_rate", 1.0),
        "warmup_iterations": test_suite_config.get("warmup_iterations", 10),
        "seed": test_suite_config.get("seed", None),
        "test_cases": test_suite_config.get("test_cases", ["chatqnafixed"]),
        "user_queries": test_suite_config.get("user_queries", [1]),
        "query_token_size": test_suite_config.get("query_token_size", 128),
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

    import importlib.util

    package_name = "opea-eval"
    spec = importlib.util.find_spec(package_name)
    print(spec)

    # get folder path of opea-eval
    eval_path = None
    import pkg_resources

    for dist in pkg_resources.working_set:
        if "opea-eval" in dist.project_name:
            eval_path = dist.location
    if not eval_path:
        print("Fail to load opea-eval package. Please install it first.")
        exit(1)

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
                "load-shape": test_params["load_shape"],
            },
            "runs": [{"name": test_phase, "users": concurrency, "max-request": num_queries}],
        }
    }

    # For the following scenarios, test will stop after the specified run-time
    if test_params["run_time"] is not None and test_phase != "warmup":
        yaml_content["profile"]["global-settings"]["run-time"] = test_params["run_time"]

    return yaml_content


def _create_stresscli_confs(case_params, test_params, test_phase, num_queries, base_url, ts) -> str:
    """Create a stresscli configuration file and persist it on disk."""
    stresscli_confs = []
    # Get the workload
    test_cases = test_params["test_cases"]
    for test_case in test_cases:
        stresscli_conf = {}
        print(test_case)
        if isinstance(test_case, str):
            bench_target = test_case
        elif isinstance(test_case, dict):
            bench_target = list(test_case.keys())[0]
            dataset_conf = test_case[bench_target]
        if bench_target == "chatqna_qlist_pubmed":
            max_lines = dataset_conf["dataset"].split("pub_med")[-1]
            stresscli_conf["envs"] = {"DATASET": f"pubmed_{max_lines}.txt", "MAX_LINES": max_lines}
        # Generate the content of stresscli configuration file
        stresscli_yaml = _create_yaml_content(case_params, base_url, bench_target, test_phase, num_queries, test_params)

        # Dump the stresscli configuration file
        service_name = case_params.get("service_name")
        run_yaml_path = os.path.join(
            test_params["test_output_dir"], f"run_{service_name}_{ts}_{test_phase}_{num_queries}_{bench_target}.yaml"
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
        for user_queries in user_queries_lst:
            stresscli_confs.extend(
                _create_stresscli_confs(service, test_suite_config, "benchmark", user_queries, base_url, index)
            )

    return stresscli_confs


def _run_service_test(example, service, test_suite_config):
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
        if stresscli_conf.get("envs") is not None:
            for key, value in stresscli_conf.get("envs").items():
                os.environ[key] = value

        output_folders.append(locust_runtests(None, run_yaml_path))

    print(f"[OPEA BENCHMARK] 🚀 Test completed for {service_name} at {url}")
    return output_folders


def run_benchmark(benchmark_config, chart_name, namespace, llm_model=None, report=False):
    # If llm_model is None or an empty string, set to default value
    if not llm_model:
        llm_model = "Qwen/Qwen2.5-Coder-7B-Instruct"

    # Extract data
    parsed_data = construct_benchmark_config(benchmark_config)
    test_suite_config = {
        "user_queries": parsed_data["user_queries"],  # num of user queries
        "random_prompt": False,  # whether to use random prompt, set to False by default
        "run_time": "60m",  # The max total run time for the test suite, set to 60m by default
        "collect_service_metric": False,  # whether to collect service metrics, set to False by default
        "llm_model": llm_model,  # The LLM model used for the test
        "deployment_type": "k8s",  # Default is "k8s", can also be "docker"
        "service_ip": None,  # Leave as None for k8s, specify for Docker
        "service_port": None,  # Leave as None for k8s, specify for Docker
        "test_output_dir": os.getcwd() + "/benchmark_output",  # The directory to store the test output
        "load_shape": {
            "name": "constant",
            "params": {"constant": {"concurrent_level": 4}, "poisson": {"arrival_rate": 1.0}},
        },
        "concurrent_level": 4,
        "arrival_rate": 1.0,
        "query_timeout": 120,
        "warm_ups": parsed_data["warmup_iterations"],
        "seed": parsed_data["seed"],
        "namespace": namespace,
        "test_cases": parsed_data["test_cases"],
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
                    "chatqna-tgi",
                ],
                "test_cases": parsed_data["test_cases"],
                # Activate if random_prompt=true: leave blank = default dataset(WebQuestions) or sharegpt
                "prompts": query_data,
                "max_output": llm_max_token,  # max number of output tokens
                "k": 1,  # number of retrieved documents
            }
        output_folder = _run_service_test(chart_name, case_data, test_suite_config)

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
    benchmark_config = load_yaml("./benchmark.yaml")
    run_benchmark(benchmark_config=benchmark_config, chart_name="chatqna", namespace="deploy-benchmark")
