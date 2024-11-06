# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import copy
import logging
import os
from typing import Any, Dict, List

import yaml
from kubernetes import client

log_level = os.getenv("LOGLEVEL", "INFO")
logging.basicConfig(level=log_level.upper(), format="%(asctime)s - %(levelname)s - %(message)s")


def replace_env_vars(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: replace_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_env_vars(v) for v in data]
    elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        env_var = data[2:-1]
        return os.getenv(env_var, "")
    else:
        return data


def convert_args_to_command(args: List[str]) -> str:
    command_parts = []
    for arg in args:
        if isinstance(arg, dict):
            for k, v in arg.items():
                command_parts.append(f"{k} {v}")
        elif isinstance(arg, str):
            command_parts.append(arg.replace(":", " "))
    return " ".join(command_parts)


def convert_resources(resources: Dict[str, Any]) -> Dict[str, Any]:
    converted_resources = {}
    for key, value in resources.items():
        if key == "hpu":
            # converted_resources['hpus'] = value
            pass
        elif key == "cpu":
            converted_resources["cpus"] = value
        elif key == "memory":
            converted_resources["memory"] = value
    return converted_resources


def extract_options(options: List[Any]) -> Dict[str, Any]:
    extracted_options = {}
    for option in options:
        if isinstance(option, dict):
            for k, v in option.items():
                if k == "cap_add":
                    extracted_options[k] = [v] if isinstance(v, str) else v
                else:
                    extracted_options[k] = v
    return extracted_options


def build_docker_compose(input_data: Dict) -> Dict:
    docker_compose = {"version": "3.8", "services": {}}

    global_envs = input_data.get("global_envs", {})

    for service in input_data.get("micro_services", []) + input_data.get("mega_service", []):
        service_name = service["service_name"]
        service_config = {
            "image": service["image"],
            "ports": service.get("ports", []),
            "volumes": service.get("volumes", []),
            "environment": global_envs.copy(),
        }

        for env in service.get("envs", []):
            if isinstance(env, list) and len(env) == 2:
                service_config["environment"][env[0]] = env[1]
            elif isinstance(env, dict):
                service_config["environment"].update(env)

        if "dependencies" in service:
            service_config["depends_on"] = service["dependencies"]

        if "replicas" in service:
            service_config["deploy"] = {"replicas": service["replicas"]}
        if "resources" in service:
            service_config["deploy"]["resources"] = {"limits": convert_resources(service.get("resources", {}))}
        if "options" in service:
            for option in service["options"]:
                for key, value in option.items():
                    if key == "cap_add":
                        service_config[key] = [value] if isinstance(value, str) else value
                    else:
                        service_config[key] = value

        if "args" in service:
            service_config["command"] = convert_args_to_command(service["args"])

        docker_compose["services"][service_name] = service_config

    return docker_compose


def convert_to_docker_compose(input_yaml_path: str, output_file: str):
    with open(input_yaml_path, "r") as file:
        input_data = yaml.safe_load(file)

    input_data = replace_env_vars(input_data)

    docker_compose_data = build_docker_compose(input_data)

    with open(output_file, "w") as file:
        yaml.dump(docker_compose_data, file, default_flow_style=False)

    print("Docker Compose file generated:", output_file)


def create_k8s_resources(
    name,
    image,
    container_ports,
    node_selector={"node-type": "opea"},
    container_name=None,
    namespace="default",
    replicas=1,
    app_label=None,
    topology_spread_constraints=None,
    args=None,
    env=None,
    env_from=[client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="qna-config"))],
    resources=None,
    volumes=None,
    volume_mounts=None,
    annotations={"sidecar.istio.io/rewriteAppHTTPProbers": "true"},
    security_context=None,
    host_ipc=True,
    image_pull_policy="IfNotPresent",
):

    if app_label is None and container_name is None:
        app_label = name
        container_name = name

    topology_spread_constraints = [
        client.V1TopologySpreadConstraint(
            max_skew=1,
            topology_key="kubernetes.io/hostname",
            when_unsatisfiable="ScheduleAnyway",
            label_selector=client.V1LabelSelector(match_labels={"app": app_label}),
        )
    ]

    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels={"app": app_label}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(annotations=annotations, labels={"app": app_label}),
                spec=client.V1PodSpec(
                    node_selector=node_selector,
                    topology_spread_constraints=topology_spread_constraints,
                    host_ipc=host_ipc,
                    service_account_name="default",
                    containers=[
                        client.V1Container(
                            name=container_name,
                            image=image,
                            image_pull_policy=image_pull_policy,
                            args=args,
                            ports=[client.V1ContainerPort(container_port=p) for p in container_ports],
                            env_from=env_from if env_from is not None else None,
                            env=env if env is not None else None,
                            resources=resources,
                            volume_mounts=volume_mounts,
                            security_context=security_context,
                        )
                    ],
                    volumes=volumes,
                ),
            ),
        ),
    )

    return deployment


def create_resource_requirements(limits=None, requests=None):
    """Create a V1ResourceRequirements object with optional limits and requests.

    :param limits: A dictionary of resource limits, e.g., {"cpu": "4", "memory": "8Gi"}
    :param requests: A dictionary of resource requests, e.g., {"cpu": "2", "memory": "4Gi"}
    :return: A V1ResourceRequirements object
    """
    return client.V1ResourceRequirements(
        limits=limits if limits is not None else None, requests=requests if requests is not None else None
    )


def create_configmap_object(config_dict=None, config_name="qna-config"):

    if config_dict is None:
        config_map = {
            "EMBEDDING_MODEL_ID": "BAAI/bge-base-en-v1.5",
            "RERANK_MODEL_ID": "BAAI/bge-reranker-base",
            "LLM_MODEL_ID": "Intel/neural-chat-7b-v3-3",
            "TEI_EMBEDDING_ENDPOINT": "http://embedding-dependency-svc.default.svc.cluster.local:6006",
            # For dataprep only
            "TEI_ENDPOINT": "http://embedding-dependency-svc.default.svc.cluster.local:6006",
            # For dataprep & retrieval & vector_db
            "INDEX_NAME": "rag-redis",
            "REDIS_URL": "redis://vector-db.default.svc.cluster.local:6379",
            "TEI_RERANKING_ENDPOINT": "http://reranking-dependency-svc.default.svc.cluster.local:8808",
            "TGI_LLM_ENDPOINT": "http://llm-dependency-svc.default.svc.cluster.local:9009",
            "HUGGINGFACEHUB_API_TOKEN": "${HF_TOKEN}",
            "EMBEDDING_SERVICE_HOST_IP": "embedding-svc",
            "RETRIEVER_SERVICE_HOST_IP": "retriever-svc",
            "RERANK_SERVICE_HOST_IP": "reranking-svc",
            "NODE_SELECTOR": "chatqna-opea",
            "LLM_SERVICE_HOST_IP": "llm-svc",
        }
    else:
        config_map = config_dict

    configmap = client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(name=config_name, namespace="default"),
        data=config_map,
    )
    return configmap


def create_service(name, app_label, service_ports, namespace="default", service_type="ClusterIP"):
    ports = []
    for port in service_ports:
        # Create a dictionary mapping to handle different field names
        port_dict = {
            "name": port.get("name"),
            "port": port.get("port"),
            "target_port": port.get("target_port"),
            "node_port": port.get("nodePort"),  # Map 'nodePort' to 'node_port'
        }

        # Remove keys with None values
        port_dict = {k: v for k, v in port_dict.items() if v is not None}

        ports.append(client.V1ServicePort(**port_dict))

    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1ServiceSpec(type=service_type, selector={"app": app_label}, ports=ports),
    )
    return service


def kubernetes_obj_to_dict(k8s_obj):
    return client.ApiClient().sanitize_for_serialization(k8s_obj)


def save_to_yaml(manifests_list, file_name):
    with open(file_name, "a") as f:
        for manifests in manifests_list:
            yaml.dump(kubernetes_obj_to_dict(manifests), f, default_flow_style=False)
            f.write("---\n")


def extract_service_configs(input_data: Dict) -> Dict:

    all_configs = {}

    global_envs = input_data.get("global_envs", {})
    all_configs["config_map"] = global_envs

    all_services = [{**s, "type": "mega_service"} for s in input_data.get("mega_service", [])] + [
        {**s, "type": "micro_service"} for s in input_data.get("micro_services", [])
    ]

    for service in all_services:
        service_name = service["service_name"]
        service_config = {
            "image": service.get("image", None),
            "ports": service.get("ports", None),
            "volumes": service.get("volumes", None),
            "node_ports": service.get("node_ports", None),
            "type": service.get("type", None),
        }

        if "envs" in service:
            result_dict = {k: str(v) for d in service["envs"] for k, v in d.items()}
            service_config["envs"] = result_dict
            all_configs["config_map"].update(result_dict)

        service_config["replicas"] = service.get("replcias", 1)
        if "resources" in service:
            resources = service.get("resources", {})
            requests = {}

            if "hpu" in service["resources"]:
                service["limits"] = {"habana.ai/gaudi": 1}

            if resources.get("cpu"):
                requests["cpu"] = resources["cpu"]
                service_config["resources"] = {"requests": requests}
            if resources.get("memory"):
                requests["memory"] = resources["memory"]
                service_config["resources"] = {"requests": requests}
            if resources.get("hpu"):
                requests["habana.ai/gaudi"] = resources["hpu"]
                service_config["resources"] = {"limits": requests}

        if "options" in service:
            for option in service["options"]:
                for key, value in option.items():
                    if key == "cap_add":
                        service_config[key] = [value] if isinstance(value, str) else value
                    else:
                        service_config[key] = value

        if "args" in service:
            service_args_list = []
            for item in service["args"]:
                if isinstance(item, dict):
                    for key, value in item.items():
                        service_args_list.extend([key, str(value)])
                else:
                    service_args_list.append(item)
            service_config["args"] = service_args_list

        logging.debug(f"{service_name} = {service_config} \n\n")
        all_configs[service_name] = service_config

    return all_configs


def create_deployment_and_service(
    service_name,
    ports,
    replicas=1,
    volume_mounts=None,
    volumes=None,
    args_list=None,
    resource_requirements=None,
    image_name=None,
    service_type="ClusterIP",
    args=None,
):

    microservice_deloyment_name = service_name + "-deploy"

    target_ports = list(set([port["target_port"] for port in ports]))

    deployment = create_k8s_resources(
        name=microservice_deloyment_name,
        image=image_name,
        replicas=replicas,
        app_label=microservice_deloyment_name,
        container_name=microservice_deloyment_name,
        container_ports=target_ports,
        node_selector={"node-type": "opea"},
        args=args_list,
        volume_mounts=volume_mounts,
        volumes=volumes,
        resources=resource_requirements,
        env_from=[client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="qna-config"))],
    )

    service = create_service(
        name=service_name,
        app_label=microservice_deloyment_name,
        service_type=service_type,
        service_ports=ports,
    )

    return deployment, service


def build_configmap(all_configs, output_file="E2E_manifest.yaml"):
    config_dict = all_configs.get("config_map", None)

    config_map = create_configmap_object(config_dict=config_dict)
    save_to_yaml([config_map], output_file)


def build_deployment_and_service(all_configs, output_file="E2E_manifest.yaml"):
    all_manifests = []
    for service_name, service_config in all_configs.items():
        if service_name == "config_map":
            continue

        image = service_config.get("image", None)
        ports = service_config.get("ports", None)
        node_ports = service_config.get("node_ports", None)
        volumes_path = service_config.get("volumes", None)
        replicas = service_config.get("replicas", None)
        resources = service_config.get("resources", None)
        envs = service_config.get("envs", None)
        options = service_config.get("options", None)
        service_args = service_config.get("args", None)
        type = service_config.get("type", None)

        if type == "micro_service":
            service_type = "ClusterIP"
        elif type == "mega_service":
            service_type = "NodePort"

        if ports is not None:
            formatted_ports = [
                {
                    "name": f"port{i+1}",
                    "port": int(p.split(":")[0]),
                    "target_port": int(p.split(":")[1]),
                    **({"nodePort": int(node_ports[i])} if node_ports and i < len(node_ports) else {}),
                }
                for i, p in enumerate(ports)
            ]

            logging.debug(f"{formatted_ports}")

        logging.debug(f"{service_args}")
        logging.debug(f"{volumes_path}")
        logging.debug(f"envs = {envs}")

        allocated_resources = None
        if resources is not None:
            if resources.get("limits", None):
                allocated_resources = create_resource_requirements(limits=resources["limits"])
            else:
                allocated_resources = create_resource_requirements(requests=resources["requests"])

        volumes = None
        volume_mounts = None
        if volumes_path:
            volumes = []
            volume_mounts = []

            # Process each path in the input list
            for i, item in enumerate(volumes_path):
                src, dest = item.split(":")

                # Create volume for the source path
                volumes.append(
                    client.V1Volume(
                        name=f"volume{i+1}",
                        host_path=client.V1HostPathVolumeSource(path=src, type="Directory"),
                    )
                )

                # Create volume mount for the destination path
                volume_mounts.append(client.V1VolumeMount(name=f"volume{i+1}", mount_path=dest))

            volumes.append(
                client.V1Volume(name="shm", empty_dir=client.V1EmptyDirVolumeSource(medium="Memory", size_limit="1Gi"))
            )
            volume_mounts.append(client.V1VolumeMount(name="shm", mount_path="/dev/shm"))

        env = [
            client.V1EnvVar(name="OMPI_MCA_btl_vader_single_copy_mechanism", value="none"),
            client.V1EnvVar(name="PT_HPU_ENABLE_LAZY_COLLECTIVES", value="true"),
            client.V1EnvVar(name="runtime", value="habana"),
            client.V1EnvVar(name="HABANA_VISIBLE_DEVICES", value="all"),
            client.V1EnvVar(name="HF_TOKEN", value="${HF_TOKEN}"),
        ]

        deployment, service = create_deployment_and_service(
            service_name=service_name,
            image_name=image,
            args_list=service_args,
            replicas=replicas,
            resource_requirements=allocated_resources,
            volumes=volumes,
            volume_mounts=volume_mounts,
            ports=formatted_ports,
            service_type=service_type,
        )
        all_manifests = [deployment, service]
        save_to_yaml(all_manifests, output_file)


def convert_to_deployment_and_service(input_yaml_path: str, output_file: str):
    with open(input_yaml_path, "r") as file:
        input_data = yaml.safe_load(file)

    input_data = replace_env_vars(input_data)
    all_configs = extract_service_configs(input_data)

    build_deployment_and_service(all_configs, output_file=output_file)

    logging.info(f" {output_file} generated:")


def convert_to_manifests(input_yaml_path: str, output_file: str):
    with open(input_yaml_path, "r") as file:
        input_data = yaml.safe_load(file)

    input_data = replace_env_vars(input_data)
    all_configs = extract_service_configs(input_data)

    build_configmap(all_configs, output_file=output_file)

    build_deployment_and_service(all_configs, output_file=output_file)

    logging.info(f" {output_file} generated:")


if __name__ == "__main__":
    with open("../../..//tests/cores/mega/mega.yaml", "r") as file:
        input_data = yaml.safe_load(file)

    input_data = replace_env_vars(input_data)
    all_configs = extract_service_configs(input_data)

    build_configmap(all_configs, output_file="E2E_manifests.yaml")

    build_deployment_and_service(all_configs, output_file="E2E_manifests.yaml")
