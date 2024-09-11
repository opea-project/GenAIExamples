# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import copy
import os

import yaml


def convert_to_docker_compose(mega_yaml, output_file, device="cpu"):
    with open(mega_yaml, "r") as f:
        mega_config = yaml.safe_load(f)

    services = {}
    env_vars = mega_config.get("environment_variables", {})

    # Define environment variable mapping for specific services
    env_var_rename = {"data_prep": {"TEI_EMBEDDING_ENDPOINT": "TEI_ENDPOINT"}}

    for service_name, service_config in mega_config["opea_micro_services"].items():
        for container_name, container_info in service_config.items():
            safe_container_name = container_name.replace("/", "-")

            # Initialize environment variables by combining 'common' with specific ones
            environment = copy.deepcopy(env_vars.get("common", {}))  # Start with 'common' vars
            # Service-specific environment (based on anchors like redis, tei_embedding, etc.)
            service_envs = container_info.get("environment", {})  # The environment anchors in the YAML
            for key, value in service_envs.items():
                environment[key] = value  # Update the environment with specific variables

            # Apply the renaming logic using the env_var_rename mapping
            renamed_environment = {}
            for key, value in environment.items():
                # If the key needs to be renamed, rename it using the mapping
                if key in env_var_rename.get(service_name, {}):
                    renamed_environment[env_var_rename[service_name][key]] = value
                else:
                    renamed_environment[key] = value

            # Replace placeholders with actual values
            for key in renamed_environment:
                if (
                    isinstance(renamed_environment[key], str)
                    and renamed_environment[key].startswith("${")
                    and renamed_environment[key].endswith("}")
                ):
                    var_name = renamed_environment[key][2:-1]
                    renamed_environment[key] = os.getenv(var_name, renamed_environment[key])

            service_entry = {
                "image": f"{container_name}:{container_info['tag']}",
                "container_name": f"{safe_container_name}-server",
                "ports": [],
                "ipc": "host",
                "restart": "unless-stopped",
                "environment": renamed_environment,
            }

            # Add ports and special settings
            if service_name == "embedding":
                service_entry["ports"].append("6000:6000")
            elif service_name == "retrieval":
                service_entry["ports"].append("7000:7000")
            elif service_name == "reranking":
                service_entry["ports"].append("8000:8000")
            elif service_name == "llm":
                service_entry["ports"].append("9000:9000")

            # Add depends_on if necessary
            if container_name == "opea/dataprep-redis":
                service_entry["depends_on"] = ["redis-vector-db"]
                service_entry["ports"].append("6007:6007")
            elif container_name == "opea/embedding-tei":
                service_entry["depends_on"] = ["tei-embedding-service"]

            # Add volumes for specific services
            if "volume" in container_info:
                service_entry["volumes"] = container_info["volume"]

            services[safe_container_name] = service_entry

    # Additional services like redis
    services["redis-vector-db"] = {
        "image": "redis/redis-stack:7.2.0-v9",
        "container_name": "redis-vector-db",
        "ports": ["6379:6379", "8001:8001"],
    }

    # Process embedding service
    embedding_service = mega_config["opea_micro_services"].get("embedding", {}).get("opea/embedding-tei", {})
    if embedding_service:
        embedding_dependencies = embedding_service.get("dependency", {})
        for dep_name, dep_info in embedding_dependencies.items():
            if dep_name == "ghcr.io/huggingface/text-embeddings-inference":
                if device == "cpu":
                    model_id = dep_info.get("requirements", {}).get("model_id", "")
                    services["text-embeddings-inference-service"] = {
                        "image": f"{dep_name}:{dep_info['tag']}",
                        "container_name": "text-embeddings-inference-server",
                        "ports": ["8090:80"],
                        "ipc": "host",
                        "environment": {
                            **env_vars.get("common", {}),
                            "HUGGINGFACEHUB_API_TOKEN": env_vars.get("HUGGINGFACEHUB_API_TOKEN", ""),
                        },
                        "command": f"--model-id {model_id} --auto-truncate",
                    }
            elif dep_name == "opea/tei-gaudi":
                if device == "gaudi":
                    model_id = dep_info.get("requirements", {}).get("model_id", "")
                    services["text-embeddings-inference-service"] = {
                        "image": f"{dep_name}:{dep_info['tag']}",
                        "container_name": "text-embeddings-inference-server",
                        "ports": ["8090:80"],
                        "ipc": "host",
                        "environment": {
                            **env_vars.get("common", {}),
                            "HUGGINGFACEHUB_API_TOKEN": env_vars.get("HUGGINGFACEHUB_API_TOKEN", ""),
                        },
                        "command": f"--model-id {model_id} --auto-truncate",
                    }
                    # Add specific settings for Habana (Gaudi) devices
                    services["text-embeddings-inference-service"]["runtime"] = "habana"
                    services["text-embeddings-inference-service"]["cap_add"] = ["SYS_NICE"]
                    services["text-embeddings-inference-service"]["environment"].update(
                        {
                            "HABANA_VISIBLE_DEVICES": "all",
                            "OMPI_MCA_btl_vader_single_copy_mechanism": "none",
                            "MAX_WARMUP_SEQUENCE_LENGTH": "512",
                            "INIT_HCCL_ON_ACQUIRE": "0",
                            "ENABLE_EXPERIMENTAL_FLAGS": "true",
                        }
                    )

    # Reranking service handling
    reranking_service = mega_config["opea_micro_services"].get("reranking", {}).get("opea/reranking-tei", {})
    if reranking_service:
        rerank_dependencies = reranking_service.get("dependency", {})
        for dep_name, dep_info in rerank_dependencies.items():
            if dep_name == "ghcr.io/huggingface/text-embeddings-inference":
                if device == "cpu":
                    model_id = dep_info.get("requirements", {}).get("model_id", "")
                    services["tei-reranking-service"] = {
                        "image": f"{dep_name}:{dep_info['tag']}",
                        "container_name": "tei-reranking-server",
                        "ports": ["8808:80"],
                        "volumes": ["./data:/data"],
                        "shm_size": "1g",
                        "environment": {
                            **env_vars.get("common", {}),
                            "HUGGINGFACEHUB_API_TOKEN": env_vars.get("HUGGINGFACEHUB_API_TOKEN", ""),
                            "HF_HUB_DISABLE_PROGRESS_BARS": "1",
                            "HF_HUB_ENABLE_HF_TRANSFER": "0",
                        },
                        "command": f"--model-id {model_id} --auto-truncate",
                    }
            elif dep_name == "opea/tei-gaudi":
                if device == "gaudi":
                    model_id = dep_info.get("requirements", {}).get("model_id", "")
                    services["tei-reranking-service"] = {
                        "image": f"{dep_name}:{dep_info['tag']}",
                        "container_name": "tei-reranking-gaudi-server",
                        "ports": ["8808:80"],
                        "volumes": ["./data:/data"],
                        "shm_size": "1g",
                        "environment": {
                            **env_vars.get("common", {}),
                            "HUGGINGFACEHUB_API_TOKEN": env_vars.get("HUGGINGFACEHUB_API_TOKEN", ""),
                            "HF_HUB_DISABLE_PROGRESS_BARS": "1",
                            "HF_HUB_ENABLE_HF_TRANSFER": "0",
                        },
                        "command": f"--model-id {model_id} --auto-truncate",
                    }
                    # Add specific settings for Habana (Gaudi) devices
                    services["tei-reranking-service"]["runtime"] = "habana"
                    services["tei-reranking-service"]["cap_add"] = ["SYS_NICE"]
                    services["tei-reranking-service"]["environment"].update(
                        {
                            "HABANA_VISIBLE_DEVICES": "all",
                            "OMPI_MCA_btl_vader_single_copy_mechanism": "none",
                            "MAX_WARMUP_SEQUENCE_LENGTH": "512",
                            "INIT_HCCL_ON_ACQUIRE": "0",
                            "ENABLE_EXPERIMENTAL_FLAGS": "true",
                        }
                    )

    # LLM service
    llm_service = mega_config["opea_micro_services"].get("llm", {}).get("opea/llm-tgi", {})
    if llm_service:
        llm_dependencies = llm_service.get("dependency", {})
        for dep_name, dep_info in llm_dependencies.items():
            if dep_name == "ghcr.io/huggingface/text-generation-inference":
                if device == "cpu":
                    model_id = dep_info.get("requirements", {}).get("model_id", "")
                    services["llm-service"] = {
                        "image": f"{dep_name}:{dep_info['tag']}",
                        "container_name": "llm-server",
                        "ports": ["9001:80"],
                        "environment": {
                            **env_vars.get("common", {}),
                            "HUGGINGFACEHUB_API_TOKEN": env_vars.get("HUGGINGFACEHUB_API_TOKEN", ""),
                        },
                        "command": f"--model-id {model_id} --max-input-length 1024 --max-total-tokens 2048",
                    }
            elif dep_name == "ghcr.io/huggingface/tgi-gaudi":
                if device == "gaudi":
                    model_id = dep_info.get("requirements", {}).get("model_id", "")
                    services["llm-service"] = {
                        "image": f"{dep_name}:{dep_info['tag']}",
                        "container_name": "llm-server",
                        "ports": ["9001:80"],
                        "environment": {
                            **env_vars.get("common", {}),
                            "HUGGINGFACEHUB_API_TOKEN": env_vars.get("HUGGINGFACEHUB_API_TOKEN", ""),
                        },
                        "command": f"--model-id {model_id} --max-input-length 1024 --max-total-tokens 2048",
                    }
                    # Add specific settings for Habana (Gaudi) devices
                    services["llm-service"]["runtime"] = "habana"
                    services["llm-service"]["cap_add"] = ["SYS_NICE"]
                    services["llm-service"]["environment"].update(
                        {
                            "HABANA_VISIBLE_DEVICES": "all",
                            "OMPI_MCA_btl_vader_single_copy_mechanism": "none",
                        }
                    )

        # Extract configuration for all examples from 'opea_mega_service'
        examples = ["chatqna", "faqgen", "audioqna", "visualqna", "codegen", "codetrans"]
        for example in examples:
            service_name = f"opea/{example}"
            ui_service_name = f"opea/{example}-ui"

            # Process both the main service and the UI service
            for service in [service_name, ui_service_name]:
                # Check if the service exists in the mega.yaml
                if service in mega_config.get("opea_mega_service", {}):
                    service_config = mega_config["opea_mega_service"][service]
                    container_name = service
                    safe_container_name = container_name.replace("/", "-")
                    tag = service_config.get("tag", "latest")
                    environment = {**env_vars.get("common", {}), **service_config.get("environment", {})}

                    service_entry = {
                        "image": f"{container_name}:{tag}",
                        "container_name": f"{safe_container_name}-server",
                        "ports": ["5173:5173"] if "-ui" in service else ["8888:8888"],
                        "ipc": "host",
                        "restart": "unless-stopped",
                        "environment": environment,
                    }
                    services[safe_container_name] = service_entry

    docker_compose = {
        "version": "3.8",
        "services": services,
        "networks": {"default": {"driver": "bridge"}},
    }

    # Write to docker-compose.yaml
    with open(output_file, "w") as f:
        yaml.dump(docker_compose, f, default_flow_style=False)

    print("Docker Compose file generated:", output_file)
