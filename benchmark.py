# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
 
import os
from datetime import datetime
 
import yaml
import sys
eval_path = '/home/sdp/GenAIEval/'
sys.path.append(eval_path)
from evals.benchmark.stresscli.commands.load_test import locust_runtests
from kubernetes import client, config


def load_yaml(file_path):
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    return data

 
def get_service_cluster_ip(service_name, namespace="default"):
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


service_endpoints = {
    "chatqna": "/v1/chatqna",
    "codegen": "/v1/codegen",
    "codetrans": "/v1/codetrans",
    "faqgen": "/v1/faqgen",
    "audioqna": "/v1/audioqna",
    "visualqna": "/v1/visualqna",
}
 
 
def extract_benchmark_config_data(content):
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
        "user_queries": test_suite_config.get("user_queries", [1]),
        "query_token_size": test_suite_config.get("query_token_size"),
        # new params
        "dataprep_chunk_size": test_suite_config.get("data_prep", {}).get("chunk_size", [1024]),
        "dataprep_chunk_overlap": test_suite_config.get("data_prep", {}).get("chunk_overlap", [1000]),
        "retriever_algo": test_suite_config.get("retriever", {}).get("algo", 'IVF'),
        "retriever_fetch_k": test_suite_config.get("retriever", {}).get("fetch_k", 2),
        "rerank_top_n": test_suite_config.get("rerank", {}).get("top_n", 2),
        "llm_max_token_size": test_suite_config.get("llm", {}).get("max_token_size", 1024),
    }
 
 
def create_run_yaml_content(service, base_url, bench_target, test_phase, num_queries, test_params):
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
                "load-shape": test_params["load_shape"],
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
 
 
def generate_stresscli_run_yaml(
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

    # Generate the content of stresscli configuration file
    stresscli_yaml = create_run_yaml_content(case_params, base_url, bench_target, test_phase, num_queries, test_params)
 
    # Dump the stresscli configuration file
    service_name = case_params.get("service_name")
    run_yaml_path = os.path.join(
        test_params["test_output_dir"], f"run_{service_name}_{ts}_{test_phase}_{num_queries}.yaml"
    )
    with open(run_yaml_path, "w") as yaml_file:
        yaml.dump(stresscli_yaml, yaml_file)
 
    return run_yaml_path
 
 
def create_and_save_run_yaml(example, deployment_type, service_type, service, base_url, test_suite_config, index):
    """Create and save the run.yaml file for the service being tested."""
    os.makedirs(test_suite_config["test_output_dir"], exist_ok=True)

    run_yaml_paths = []
 
    # Add YAML configuration of stresscli for warm-ups
    warm_ups = test_suite_config["warm_ups"]
    if warm_ups is not None and warm_ups > 0:
        run_yaml_paths.append(
            generate_stresscli_run_yaml(
                example, service_type, service, test_suite_config, "warmup", warm_ups, base_url, index
            )
        )

    # Add YAML configuration of stresscli for benchmark
    user_queries_lst = test_suite_config["user_queries"]
    if user_queries_lst is None or len(user_queries_lst) == 0:
        # Test stop is controlled by run time
        run_yaml_paths.append(
            generate_stresscli_run_yaml(
                example, service_type, service, test_suite_config, "benchmark", -1, base_url, index
            )
        )
    else:
        # Test stop is controlled by request count
        for user_queries in user_queries_lst:
            run_yaml_paths.append(
                generate_stresscli_run_yaml(
                    example, service_type, service, test_suite_config, "benchmark", user_queries, base_url, index
                )
            )
 
    return run_yaml_paths
 
 
def get_service_ip(service_name, deployment_type="k8s", service_ip=None, service_port=None, namespace="default"):
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
        svc_ip, port = get_service_cluster_ip(service_name, namespace)
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
 
 
def run_service_test(example, service_type, service, test_suite_config):
 
    # Get the service name
    service_name = service.get("service_name")
 
    # Get the deployment type from the test suite configuration
    deployment_type = test_suite_config.get("deployment_type", "k8s")
 
    # Get the service IP and port based on deployment type
    svc_ip, port = get_service_ip(
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
    run_yaml_paths = create_and_save_run_yaml(
        example, deployment_type, service_type, service, base_url, test_suite_config, timestamp
    )

    # Run the test using locust_runtests function
    output_folders = []
    for index, run_yaml_path in enumerate(run_yaml_paths, start=1):
        print(f"[OPEA BENCHMARK] 🚀 The {index} time test is running, run yaml: {run_yaml_path}...")
        output_folders.append(locust_runtests(None, run_yaml_path))
 
    print(f"[OPEA BENCHMARK] 🚀 Test completed for {service_name} at {url}")
 
    return output_folders
 
 
def process_service(example, service_type, case_data, test_suite_config):
    print(f"[OPEA BENCHMARK] 🚀 Example: [ {example} ] Service: [ {case_data.get('service_name')} ], Running test...")
    return run_service_test(example, service_type, case_data, test_suite_config)
 
 
def run_benchmark(benchmark_config, report=False):
    # Extract data
    parsed_data = extract_benchmark_config_data(benchmark_config)
    os.environ['MAX_TOKENS'] = str(parsed_data['llm_max_token_size'])
    test_suite_config = {
        "user_queries": parsed_data["user_queries"],  # num of user queries set to 1 by default
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
        "max_output": parsed_data['llm_max_token_size'],  # max number of output tokens
        "k": 1 # number of retrieved documents
    }
    output_folder = process_service(parsed_data["example_name"], service_type, case_data, test_suite_config)
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
    run_benchmark(benchmark_config)
 