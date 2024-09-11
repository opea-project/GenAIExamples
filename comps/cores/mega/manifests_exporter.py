# # Copyright (C) 2024 Intel Corporation
# # SPDX-License-Identifier: Apache-2.0
import argparse

import yaml
from kubernetes import client


def load_service_info(file_path=None):
    if file_path:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        return data

    return None


def create_k8s_resources(
    name,
    image,
    container_ports,
    node_selector={"node-type": "chatqna-opea"},
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


def create_configmap_object(service_info=None):

    if service_info is None:
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

    configmap = client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(name="qna-config", namespace="default"),
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


def create_embedding_deployment_and_service(resource_requirements=None, replicas=None):

    args = ["--model-id", "$(EMBEDDING_MODEL_ID)", "--auto-truncate"]
    volume_mounts = [
        client.V1VolumeMount(name="model-volume", mount_path="/data"),
        client.V1VolumeMount(name="shm", mount_path="/dev/shm"),
    ]

    volumes = [
        client.V1Volume(
            name="model-volume",
            host_path=client.V1HostPathVolumeSource(path="/mnt/models", type="Directory"),
        ),
        client.V1Volume(name="shm", empty_dir=client.V1EmptyDirVolumeSource(medium="Memory", size_limit="1Gi")),
    ]

    deployment = create_k8s_resources(
        name="embedding-dependency-deploy",
        replicas=1,
        app_label="embedding-dependency-deploy",
        image="ghcr.io/huggingface/text-embeddings-inference:cpu-1.5",
        container_name="embedding-dependency-deploy",
        container_ports=[80],
        node_selector={"node-type": "chatqna-opea"},
        resources=resource_requirements,
        env_from=[client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="qna-config"))],
        args=args,
        volume_mounts=volume_mounts,
        volumes=volumes,
    )

    embedding_dependency_ports = [
        {
            "name": "service",
            "port": 6006,
            "target_port": 80,
        },
    ]
    service = create_service(
        name="embedding-dependency-svc",
        app_label="embedding-dependency-deploy",
        service_ports=embedding_dependency_ports,
    )

    return deployment, service


def create_embedding_svc_deployment_and_service(resource_requirements=None, replicas=None):

    deployment = create_k8s_resources(
        name="embedding-deploy",
        replicas=1,
        image="opea/embedding-tei:latest",
        container_ports=[6000],
        resources=resource_requirements,
        env_from=[client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="qna-config"))],
    )

    ports = [
        {
            "name": "service",
            "port": 6000,
            "target_port": 6000,
        },
    ]
    service = create_service(name="embedding-svc", app_label="embedding-deploy", service_ports=ports)

    return deployment, service


def create_llm_dependency_deployment_and_service(resource_requirements=None, replicas=None):

    args = [
        "--model-id",
        "$(LLM_MODEL_ID)",
        "--max-input-length",
        "1024",
        "--max-total-tokens",
        "2048",
        "--max-batch-total-tokens",
        "65536",
        "--max-batch-prefill-tokens",
        "4096",
    ]

    volume_mounts = [
        client.V1VolumeMount(mount_path="/data", name="model-volume"),
        client.V1VolumeMount(mount_path="/dev/shm", name="shm"),
    ]

    env = [
        client.V1EnvVar(name="OMPI_MCA_btl_vader_single_copy_mechanism", value="none"),
        client.V1EnvVar(name="PT_HPU_ENABLE_LAZY_COLLECTIVES", value="true"),
        client.V1EnvVar(name="runtime", value="habana"),
        client.V1EnvVar(name="HABANA_VISIBLE_DEVICES", value="all"),
        client.V1EnvVar(name="HF_TOKEN", value="${HF_TOKEN}"),
    ]

    volumes = [
        client.V1Volume(
            name="model-volume",
            host_path=client.V1HostPathVolumeSource(path="/mnt/models", type="Directory"),
        ),
        client.V1Volume(name="shm", empty_dir=client.V1EmptyDirVolumeSource(medium="Memory", size_limit="1Gi")),
    ]

    security_context = client.V1SecurityContext(capabilities=client.V1Capabilities(add=["SYS_NICE"]))
    deployment = create_k8s_resources(
        name="llm-dependency-deploy",
        replicas=7,
        image="ghcr.io/huggingface/tgi-gaudi:2.0.4",
        container_ports=[80],
        node_selector={"node-type": "chatqna-opea"},
        resources=resource_requirements,
        env_from=[client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="qna-config"))],
        env=env,
        args=args,
        volume_mounts=volume_mounts,
        volumes=volumes,
        security_context=security_context,
    )

    ports = [
        {
            "name": "service",
            "port": 9009,
            "target_port": 80,
        },
    ]
    service = create_service(name="llm-dependency-svc", app_label="llm-dependency-deploy", service_ports=ports)

    return deployment, service


def create_reranking_dependency_deployment_and_service(resource_requirements=None, replicas=None):

    args = ["--model-id", "$(RERANK_MODEL_ID)", "--auto-truncate"]

    volume_mounts = [
        client.V1VolumeMount(mount_path="/data", name="model-volume"),
        client.V1VolumeMount(mount_path="/dev/shm", name="shm"),
    ]

    env = [
        client.V1EnvVar(name="OMPI_MCA_btl_vader_single_copy_mechanism", value="none"),
        client.V1EnvVar(name="PT_HPU_ENABLE_LAZY_COLLECTIVES", value="true"),
        client.V1EnvVar(name="runtime", value="habana"),
        client.V1EnvVar(name="HABANA_VISIBLE_DEVICES", value="all"),
        client.V1EnvVar(name="HF_TOKEN", value="${HF_TOKEN}"),
        client.V1EnvVar(name="MAX_WARMUP_SEQUENCE_LENGTH", value="512"),
    ]

    volumes = [
        client.V1Volume(
            name="model-volume",
            host_path=client.V1HostPathVolumeSource(path="/mnt/models", type="Directory"),
        ),
        client.V1Volume(name="shm", empty_dir=client.V1EmptyDirVolumeSource(medium="Memory", size_limit="1Gi")),
    ]

    volume_mounts = [
        client.V1VolumeMount(mount_path="/data", name="model-volume"),
        client.V1VolumeMount(mount_path="/dev/shm", name="shm"),
    ]

    deployment = create_k8s_resources(
        name="reranking-dependency-deploy",
        replicas=1,
        image="opea/tei-gaudi:latest",
        container_ports=[80],
        node_selector={"node-type": "chatqna-opea"},
        resources=resource_requirements,
        env_from=[client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="qna-config"))],
        env=env,
        args=args,
        volume_mounts=volume_mounts,
        volumes=volumes,
    )

    ports = [
        {
            "name": "service",
            "port": 8808,
            "target_port": 80,
        },
    ]
    service = create_service(
        name="reranking-dependency-svc", app_label="reranking-dependency-deploy", service_ports=ports
    )

    return deployment, service


def create_llm_deployment_and_service(resource_requirements=None, replicas=None):

    deployment = create_k8s_resources(
        name="llm-deploy",
        replicas=1,
        image="opea/llm-tgi:latest",
        container_ports=[9000],
        resources=resource_requirements,
    )

    ports = [
        {
            "name": "service",
            "port": 9000,
            "target_port": 9000,
        },
    ]
    service = create_service(name="llm-svc", app_label="llm-deploy", service_ports=ports)

    return deployment, service


def create_dataprep_deployment_and_service(resource_requirements=None, replicas=None):
    deployment = create_k8s_resources(
        name="dataprep-deploy",
        namespace="default",
        replicas=1,
        app_label="dataprep-deploy",
        image="opea/dataprep-redis:latest",
        container_name="dataprep-deploy",
        container_ports=[6007],
        node_selector={"node-type": "chatqna-opea"},
        resources=resource_requirements,
    )

    ports = [{"name": "port1", "port": 6007, "target_port": 6007}]
    service = create_service(name="dataprep-svc", app_label="dataprep-deploy", service_ports=ports)

    return deployment, service


def create_chatqna_mega_deployment(resource_requirements=None, replicas=None):

    deployment = create_k8s_resources(
        name="chatqna-backend-server-deploy",
        replicas=1,
        app_label="chatqna-backend-server-deploy",
        image="opea/chatqna:latest",
        container_name="chatqna-backend-server-deploy",
        container_ports=[8888],
        node_selector={"node-type": "chatqna-opea"},
        resources=resource_requirements,
        env_from=[client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="qna-config"))],
    )

    ports = [
        {"name": "service", "port": 8888, "target_port": 8888, "nodePort": 30888},
    ]
    service = create_service(
        name="chatqna-backend-server-svc",
        app_label="chatqna-backend-server-deploy",
        service_type="NodePort",
        service_ports=ports,
    )

    return deployment, service


def create_reranking_deployment_and_service(resource_requirements=None, replicas=None):
    deployment = create_k8s_resources(
        name="reranking-deploy",
        replicas=1,
        image="opea/reranking-tei:latest",
        container_ports=[8000],
        resources=resource_requirements,
    )

    ports = [
        {
            "name": "service",
            "port": 8000,
            "target_port": 8000,
        },
    ]
    service = create_service(name="reranking-svc", app_label="reranking-deploy", service_ports=ports)

    return deployment, service


def create_retriever_deployment_and_service(resource_requirements=None, replicas=None):

    deployment = create_k8s_resources(
        name="retriever-deploy",
        replicas=1,
        image="opea/retriever-redis:latest",
        container_ports=[7000],
        resources=resource_requirements,
    )

    ports = [
        {
            "name": "service",
            "port": 7000,
            "target_port": 7000,
        },
    ]
    service = create_service(name="retriever-svc", app_label="retriever-deploy", service_ports=ports)

    return deployment, service


def create_vector_db_deployment_and_service(resource_requirements=None, replicas=None):

    deployment = create_k8s_resources(
        name="vector-db",
        replicas=1,
        image="redis/redis-stack:7.2.0-v9",
        container_ports=[6379, 8001],
        resources=resource_requirements,
    )

    ports = [
        {"name": "vector-db-service", "port": 6379, "target_port": 6379},
        {"name": "vector-db-insight", "port": 8001, "target_port": 8001},
    ]
    service = create_service(name="vector-db", app_label="vector-db", service_ports=ports)

    return deployment, service


def kubernetes_obj_to_dict(k8s_obj):
    return client.ApiClient().sanitize_for_serialization(k8s_obj)


def save_to_yaml(manifests_list, file_name):
    with open(file_name, "w") as f:
        for manifests in manifests_list:
            yaml.dump(kubernetes_obj_to_dict(manifests), f, default_flow_style=False)
            f.write("---\n")


def build_chatqna_manifests(service_info=None):
    configmap = create_configmap_object(service_info)

    guaranteed_resource = create_resource_requirements(
        limits={"cpu": 8, "memory": "8000Mi"}, requests={"cpu": 8, "memory": "8000Mi"}
    )

    burstable_resource = create_resource_requirements(requests={"cpu": 4, "memory": "4000Mi"})

    # Microservice
    chatqna_deploy, chatqna_svc = create_chatqna_mega_deployment(guaranteed_resource)
    embedding_deploy, embedding_deploy_svc = create_embedding_svc_deployment_and_service(burstable_resource)
    reranking_svc, reranking_svc_svc = create_reranking_deployment_and_service(burstable_resource)
    lm_deploy, lm_deploy_svc = create_llm_deployment_and_service(burstable_resource)

    # Embedding, Reranking and LLM
    embedding_dependency_resource = create_resource_requirements(
        limits={"cpu": 80, "memory": "20000Mi"}, requests={"cpu": 80, "memory": "20000Mi"}
    )
    embedding_dependency, embedding_dependency_svc = create_embedding_deployment_and_service(
        embedding_dependency_resource
    )

    llm_hpu_resource_requirements = create_resource_requirements(limits={"habana.ai/gaudi": 1})
    llm_dependency, llm_dependency_svc = create_llm_dependency_deployment_and_service(llm_hpu_resource_requirements)

    reranking_hpu_resource_requirements = create_resource_requirements(limits={"habana.ai/gaudi": 1})
    reranking_depn_deployment, reranking_depn_service = create_reranking_dependency_deployment_and_service(
        reranking_hpu_resource_requirements
    )

    retrieval_deployment, retrieval_svc = create_retriever_deployment_and_service(burstable_resource)
    vector_db_deploy, vector_db_svc = create_vector_db_deployment_and_service()
    dataprep_deploy, dataprep_svc = create_dataprep_deployment_and_service()

    manifests = [
        configmap,
        chatqna_deploy,
        chatqna_svc,
        dataprep_deploy,
        dataprep_svc,
        embedding_dependency,
        embedding_dependency_svc,
        embedding_deploy,
        embedding_deploy_svc,
        llm_dependency,
        llm_dependency_svc,
        lm_deploy,
        lm_deploy_svc,
        reranking_depn_deployment,
        reranking_depn_service,
        reranking_svc,
        reranking_svc_svc,
        retrieval_deployment,
        retrieval_svc,
        vector_db_deploy,
        vector_db_svc,
    ]

    save_to_yaml(manifests, "ChatQnA_E2E_manifests.yaml")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read and parse JSON/YAML files and output JSON file")
    parser.add_argument("--service_info", help="Path to input YAML file")

    args = parser.parse_args()

    service_info = load_service_info(args.service_info)

    build_chatqna_manifests(service_info)
