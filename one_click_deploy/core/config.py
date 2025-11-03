# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import os
import pathlib

# Project structure paths
SCRIPT_ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES_ROOT_DIR = SCRIPT_ROOT_DIR.parent
COMMON_SCRIPTS_DIR = SCRIPT_ROOT_DIR / "common"
LOG_FILE_PATH = SCRIPT_ROOT_DIR / "deployment.log"

EXAMPLE_CONFIGS = {
    "ChatQnA": {
        "base_dir": "ChatQnA",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose.yaml",
                    "gaudi": "docker_compose/intel/hpu/gaudi/compose.yaml",
                },
                "openeuler": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose_openeuler.yaml",
                },
            },
            "set_env_scripts": {
                "xeon": "docker_compose/intel/cpu/xeon/set_env.sh",
                "gaudi": "docker_compose/intel/hpu/gaudi/set_env.sh",
            },
            "params_to_set_env": {
                "llm_model": "LLM_MODEL_ID",
                "embed_model": "EMBEDDING_MODEL_ID",
                "rerank_model": "RERANK_MODEL_ID",
                "mount_dir": "MOUNT_DIR",
                "hf_token": "HF_TOKEN",
            },
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/chatqna",
                "values_files": {
                    "debian": {
                        "xeon": "kubernetes/helm/cpu-values.yaml",
                        "gaudi": "kubernetes/helm/gaudi-values.yaml",
                    },
                    "openeuler": {
                        "xeon": "kubernetes/helm/cpu-openeuler-values.yaml",
                    },
                },
                "params_to_values": {
                    "hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"],
                    "llm_model": ["vllm", "LLM_MODEL_ID"],
                    "embed_model": ["tei", "EMBEDDING_MODEL_ID"],
                    "rerank_model": ["teirerank", "RERANK_MODEL_ID"],
                },
            },
            "namespace": "chatqna",
            "release_name": "chatqna",
            "ui_namespace": "rag-ui",
        },
        "supported_os": ["debian", "openeuler"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
            "openeuler": ["xeon"],
        },
        "default_device": "xeon",
        "offline_support": ["docker"],
        "ports": {
            "docker": {
                "backend": "8888",
                "dataprep": "11101",
                "embedding": "6000",
                "retriever": "7000",
                "reranking": "8000",
                "llm": "9009",
            },
            "k8s_services": {
                "backend": "chatqna",
                "dataprep": "dataprep-svc",
                "embedding": "embedding-mosec-svc",
                "retriever": "retriever-svc",
                "reranking": "reranking-mosec-svc",
                "llm": "llm-dependency-svc",
            },
        },
        "test_connections": {
            "main_service": {
                "service_key": "backend",
                "path": "/v1/chatqna",
                "method": "POST",
                "payload": {
                    "messages": [{"role": "user", "content": "What is Nike's revenue?"}],
                    "max_new_tokens": 100,
                },
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
            "sub_services": [
                {
                    "name": "llm_check",
                    "service_key": "llm",
                    "path": "/v1/chat/completions",
                    "method": "POST",
                    "payload_dynamic_llm_model": True,
                    "default_llm_model_id_for_test": "meta-llama/Meta-Llama-3-8B-Instruct",
                    "payload_template": {"messages": [{"role": "user", "content": "Deep Learning?"}], "max_tokens": 17},
                    "headers": {"Content-Type": "application/json"},
                    "expect_code": 200,
                    "expect_response_contains": "content",
                }
            ],
        },
        "interactive_params": [
            {
                "name": "llm_model",
                "prompt": "LLM Model ID",
                "type": str,
                "help": "e.g., meta-llama/Meta-Llama-3-8B-Instruct",
            },
            {
                "name": "embed_model",
                "prompt": "Embedding Model ID",
                "type": str,
                "help": "e.g., BAAI/bge-base-en-v1.5",
            },
            {
                "name": "rerank_model",
                "prompt": "Reranking Model ID",
                "type": str,
                "help": "e.g., BAAI/bge-reranker-base",
            },
            {
                "name": "mount_dir",
                "prompt": "Data Mount Directory (for Docker)",
                "type": str,
                "default": "./data",
                "modes": ["docker"],
            },
        ],
    },
    "CodeTrans": {
        "base_dir": "CodeTrans",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose.yaml",
                    "gaudi": "docker_compose/intel/hpu/gaudi/compose.yaml",
                },
            },
            "set_env_scripts": {"xeon": "docker_compose/intel/set_env.sh", "gaudi": "docker_compose/intel/set_env.sh"},
            "params_to_set_env": {"llm_model": "LLM_MODEL_ID", "hf_token": "HF_TOKEN"},
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/codetrans",
                "values_files": {
                    "debian": {
                        "xeon": "kubernetes/helm/cpu-values.yaml",
                        "gaudi": "kubernetes/helm/gaudi-values.yaml",
                    },
                },
                "params_to_values": {
                    "hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"],
                    "llm_model": [["llm-uservice", "LLM_MODEL_ID"], ["vllm", "LLM_MODEL_ID"]],
                },
            },
            "namespace": "codetrans",
            "release_name": "codetrans",
        },
        "supported_os": ["debian"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
        },
        "default_device": "xeon",
        "offline_support": [],
        "ports": {
            "docker": {"backend": "7777", "llm": "9000"},
            "k8s_services": {"backend": "codetrans", "llm": "codetrans-llm-svc"},
        },
        "test_connections": {
            "main_service": {
                "service_key": "backend",
                "path": "/v1/codetrans",
                "method": "POST",
                "payload": {
                    "source_code": "def hello():\n  print('world')",
                    "language_from": "python",
                    "language_to": "javascript",
                },
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
            "sub_services": [
                {
                    "name": "llm_code_trans_check",
                    "service_key": "llm",
                    "path": "/v1/completions",
                    "method": "POST",
                    "payload_dynamic_llm_model": True,
                    "default_llm_model_id_for_test": "mistralai/Mistral-7B-Instruct-v0.3",
                    "payload_template": {
                        "prompt": "Translate to Python: function add(a, b) { return a + b; }",
                        "max_tokens": 50,
                    },
                    "headers": {"Content-Type": "application/json"},
                    "expect_code": 200,
                }
            ],
        },
        "interactive_params": [
            {
                "name": "llm_model",
                "prompt": "LLM Model ID (for Code Translation)",
                "type": str,
                "help": "e.g., mistralai/Mistral-7B-Instruct-v0.3",
            },
        ],
    },
    "DocSum": {
        "base_dir": "DocSum",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose.yaml",
                    "gaudi": "docker_compose/intel/hpu/gaudi/compose.yaml",
                },
            },
            "set_env_scripts": {"xeon": "docker_compose/intel/set_env.sh", "gaudi": "docker_compose/intel/set_env.sh"},
            "params_to_set_env": {"llm_model": "LLM_MODEL_ID", "hf_token": "HF_TOKEN"},
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/docsum",
                "values_files": {
                    "debian": {
                        "xeon": "kubernetes/helm/cpu-values.yaml",
                        "gaudi": "kubernetes/helm/gaudi-values.yaml",
                    },
                },
                "params_to_values": {
                    "hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"],
                    "llm_model": [["llm-uservice", "LLM_MODEL_ID"], ["vllm", "LLM_MODEL_ID"]],
                },
            },
            "namespace": "docsum",
            "release_name": "docsum",
        },
        "supported_os": ["debian"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
        },
        "default_device": "xeon",
        "offline_support": [],
        "ports": {
            "docker": {"backend": "8888", "llm": "8008"},
            "k8s_services": {"backend": "docsum", "llm": "llm-docsum-svc"},
        },
        "test_connections": {
            "main_service": {
                "service_key": "backend",
                "path": "/v1/docsum",
                "method": "POST",
                "payload": {
                    "type": "audio",
                    "messages": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA",
                },
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
            "sub_services": [
                {
                    "name": "llm_docsum_check",
                    "service_key": "llm",
                    "path": "/v1/completions",
                    "method": "POST",
                    "payload_dynamic_llm_model": True,
                    "default_llm_model_id_for_test": "meta-llama/Meta-Llama-3-8B-Instruct",
                    "payload_template": {
                        "prompt": "Summarize this: The quick brown fox jumps over the lazy dog.",
                        "max_tokens": 50,
                    },
                    "headers": {"Content-Type": "application/json"},
                    "expect_code": 200,
                }
            ],
        },
        "interactive_params": [
            {
                "name": "llm_model",
                "prompt": "LLM Model ID (for DocSum)",
                "type": str,
                "help": "e.g., meta-llama/Meta-Llama-3-8B-Instruct",
            },
        ],
    },
    "CodeGen": {
        "base_dir": "CodeGen",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose.yaml",
                    "gaudi": "docker_compose/intel/hpu/gaudi/compose.yaml",
                },
                "openeuler": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose_openeuler.yaml",
                },
            },
            "set_env_scripts": {"xeon": "docker_compose/intel/set_env.sh", "gaudi": "docker_compose/intel/set_env.sh"},
            "params_to_set_env": {"llm_model": "LLM_MODEL_ID", "hf_token": "HF_TOKEN"},
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/codegen",
                "values_files": {
                    "debian": {
                        "xeon": "kubernetes/helm/cpu-values.yaml",
                        "gaudi": "kubernetes/helm/gaudi-values.yaml",
                    },
                    "openeuler": {
                        "xeon": "kubernetes/helm/cpu-openeuler-values.yaml",
                    },
                },
                "params_to_values": {
                    "hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"],
                    "llm_model": [["llm-uservice", "LLM_MODEL_ID"], ["vllm", "LLM_MODEL_ID"]],
                },
            },
            "namespace": "codegen",
            "release_name": "codegen",
        },
        "supported_os": ["debian", "openeuler"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
            "openeuler": ["xeon"],
        },
        "default_device": "xeon",
        "offline_support": [],
        "ports": {
            "docker": {"backend": "7778", "llm": "8028"},
            "k8s_services": {"backend": "codegen", "llm": "codegen-llm-uservice"},
        },
        "test_connections": {
            "main_service": {
                "service_key": "backend",
                "path": "/v1/codegen",
                "method": "POST",
                "payload": {"messages": "Write a Python function that adds two numbers."},
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
            "sub_services": [
                {
                    "name": "llm_code_gen_check",
                    "service_key": "llm",
                    "path": "/v1/completions",
                    "method": "POST",
                    "payload_dynamic_llm_model": True,
                    "default_llm_model_id_for_test": "Qwen/Qwen2.5-Coder-7B-Instruct",
                    "payload_template": {
                        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
                        "messages": [{"role": "user", "content": "Implement a basic Python class"}],
                        "max_tokens": 32,
                    },
                    "headers": {"Content-Type": "application/json"},
                    "expect_code": 200,
                }
            ],
        },
        "interactive_params": [
            {
                "name": "llm_model",
                "prompt": "LLM Model ID (for Code Generation)",
                "type": str,
                "help": "e.g., Qwen/Qwen2.5-Coder-7B-Instruct",
            },
        ],
    },
    "AudioQnA": {
        "base_dir": "AudioQnA",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose.yaml",
                    "gaudi": "docker_compose/intel/hpu/gaudi/compose.yaml",
                },
                "openeuler": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose_openeuler.yaml",
                },
            },
            "set_env_scripts": {
                "xeon": "docker_compose/intel/cpu/xeon/set_env.sh",
                "gaudi": "docker_compose/intel/hpu/gaudi/set_env.sh",
            },
            "params_to_set_env": {"llm_model": "LLM_MODEL_ID", "hf_token": "HF_TOKEN"},
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/audioqna",
                "values_files": {
                    "debian": {
                        "xeon": "kubernetes/helm/cpu-values.yaml",
                        "gaudi": "kubernetes/helm/gaudi-values.yaml",
                    },
                    "openeuler": {
                        "xeon": "kubernetes/helm/cpu-openeuler-values.yaml",
                    },
                },
                "params_to_values": {
                    "hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"],
                    "llm_model": [["llm-uservice", "LLM_MODEL_ID"], ["vllm", "LLM_MODEL_ID"]],
                },
            },
            "namespace": "audioqna",
            "release_name": "audioqna",
        },
        "supported_os": ["debian", "openeuler"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
            "openeuler": ["xeon"],
        },
        "default_device": "xeon",
        "offline_support": [],
        "ports": {
            "docker": {"backend": "3008", "llm": "3006"},
            "k8s_services": {"backend": "audioqna", "llm": "audioqna-vllm"},
        },
        "test_connections": {
            "main_service": {
                "service_key": "backend",
                "path": "/v1/audioqna",
                "method": "POST",
                "payload": {
                    "audio": "https://github.com/intel/intel-extension-for-transformers/raw/refs/heads/main/intel_extension_for_transformers/neural_chat/assets/audio/sample_2.wav",
                    "max_tokens": 64,
                    "voice": "default",
                },
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
            "sub_services": [
                {
                    "name": "llm_audio_qna_check",
                    "service_key": "llm",
                    "path": "/v1/completions",
                    "method": "POST",
                    "payload_dynamic_llm_model": True,
                    "default_llm_model_id_for_test": "Qwen/Qwen2.5-Coder-7B-Instruct",
                    "payload_template": {
                        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
                        "messages": [{"role": "user", "content": "Implement a basic Python class"}],
                        "max_tokens": 32,
                    },
                    "headers": {"Content-Type": "application/json"},
                    "expect_code": 200,
                }
            ],
        },
        "interactive_params": [
            {
                "name": "llm_model",
                "prompt": "LLM Model ID (for Audio Q&A)",
                "type": str,
                "help": "e.g., meta-llama/Meta-Llama-3-8B-Instruct",
            },
        ],
    },
    "VisualQnA": {
        "base_dir": "VisualQnA",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose.yaml",
                    "gaudi": "docker_compose/intel/hpu/gaudi/compose.yaml",
                },
            },
            "set_env_scripts": {
                "xeon": "docker_compose/intel/cpu/xeon/set_env.sh",
                "gaudi": "docker_compose/intel/hpu/gaudi/set_env.sh",
            },
            "params_to_set_env": {"lvm_model": "LVM_MODEL_ID", "hf_token": "HF_TOKEN"},
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/visualqna",
                "values_files": {
                    "debian": {
                        "xeon": "kubernetes/helm/cpu-values.yaml",
                        "gaudi": "kubernetes/helm/gaudi-values.yaml",
                    },
                },
                "params_to_values": {"hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"]},
            },
            "namespace": "visualqna",
            "release_name": "visualqna",
        },
        "supported_os": ["debian"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
        },
        "default_device": "xeon",
        "offline_support": [],
        "ports": {
            "docker": {"backend": "8888", "lvm": "9399", "nginx": "81"},
            "k8s_services": {"backend": "visualqna", "lvm": "visualqna-lvm-uservice"},
        },
        "test_connections": {
            "main_service": {
                "service_key": "backend",
                "path": "/v1/visualqna",
                "method": "POST",
                "payload": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What'''s in this image?"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 300,
                },
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
            "sub_services": [
                {
                    "name": "lvm_visual_qna_check",
                    "service_key": "lvm",
                    "path": "/v1/lvm",
                    "method": "POST",
                    "payload_template": {"image": "", "prompt": "What is deep learning?"},
                    "headers": {"Content-Type": "application/json"},
                    "expect_code": 200,
                }
            ],
        },
        "interactive_params": [
            {
                "name": "lvm_model",
                "prompt": "LVM Model ID (for Visual Q&A)",
                "type": str,
                "help": "e.g., llava-hf/llava-v1.6-mistral-7b-hf",
            },
        ],
    },
    "FaqGen": {
        "base_dir": "ChatQnA",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": "docker_compose/intel/cpu/xeon/compose_faqgen.yaml",
                    "gaudi": "docker_compose/intel/hpu/gaudi/compose_faqgen.yaml",
                },
            },
            "set_env_scripts": {
                "xeon": "docker_compose/intel/cpu/xeon/set_env.sh",
                "gaudi": "docker_compose/intel/hpu/gaudi/set_env_faqgen.sh",
            },
            "params_to_set_env": {
                "llm_model": "LLM_MODEL_ID",
                "hf_token": "HF_TOKEN",
            },
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/chatqna",
                "values_files": {
                    "debian": {
                        "xeon": "kubernetes/helm/faqgen-cpu-values.yaml",
                        "gaudi": "kubernetes/helm/faqgen-gaudi-values.yaml",
                    },
                },
                "params_to_values": {
                    "hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"],
                    "llm_model": [["llm-uservice", "LLM_MODEL_ID"], ["vllm", "LLM_MODEL_ID"]],
                },
            },
            "namespace": "faqgen",
            "release_name": "faqgen",
        },
        "supported_os": ["debian"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
        },
        "default_device": "xeon",
        "offline_support": [],
        "ports": {
            "docker": {
                "backend": "8888",
                "llm": "9000",
            },
            "k8s_services": {
                "backend": "faqgen-chatqna",
                "llm": "faqgen-llm-uservice",
            },
        },
        "test_connections": {
            "main_service": {
                "service_key": "backend",
                "path": "/v1/chatqna",
                "method": "POST",
                "payload": {
                    "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.",
                    "max_tokens": 32,
                    "stream": False,
                },
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
            "sub_services": [
                {
                    "name": "llm_check",
                    "service_key": "llm",
                    "path": "/v1/faqgen",
                    "method": "POST",
                    "payload_template": {
                        "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."
                    },
                    "headers": {"Content-Type": "application/json"},
                    "expect_code": 200,
                    "expect_response_contains": "content",
                }
            ],
        },
        "interactive_params": [
            {
                "name": "llm_model",
                "prompt": "LLM Model ID",
                "type": str,
                "help": "e.g., meta-llama/Meta-Llama-3-8B-Instruct",
            },
        ],
    },
    "AgentQnA": {
        "base_dir": "AgentQnA",
        "docker_compose": {
            "paths": {
                "debian": {
                    "xeon": [
                        "docker_compose/intel/cpu/xeon/compose_openai.yaml",
                        f"{EXAMPLES_ROOT_DIR}/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml",
                    ],
                    "gaudi": [
                        "docker_compose/intel/hpu/gaudi/compose.yaml",
                        f"{EXAMPLES_ROOT_DIR}/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml",
                    ],
                }
            },
            "set_env_scripts": {
                "xeon": "docker_compose/intel/cpu/xeon/set_env.sh",
                "gaudi": "docker_compose/intel/hpu/gaudi/set_env.sh",
            },
            "params_to_set_env": {
                "xeon": {
                    "openai_api_key": "OPENAI_API_KEY",
                    "hf_token": "HF_TOKEN",
                },
                "gaudi": {
                    "llm_model": "LLM_MODEL_ID",
                    "hf_token": "HF_TOKEN",
                    "num_shards": "NUM_SHARDS",
                },
            },
        },
        "kubernetes": {
            "helm": {
                "chart_oci": "oci://ghcr.io/opea-project/charts/agentqna",
                "values_files": {
                    "debian": {
                        "gaudi": "kubernetes/helm/gaudi-values.yaml",
                    },
                },
                "params_to_values": {
                    "llm_model": [
                        ["vllm", "LLM_MODEL_ID"],
                        ["supervisor", "model"],
                        ["ragagent", "model"],
                        ["sqlagent", "model"],
                    ],
                    "hf_token": ["global", "HUGGINGFACEHUB_API_TOKEN"],
                    "num_shards": ["vllm", "resources", "limits", "habana.ai/gaudi"],
                },
            },
            "namespace": "agentqna",
            "release_name": "agentqna",
            "ui_namespace": "agentqna-ui",
        },
        "supported_os": ["debian"],
        "default_os": "debian",
        "supported_devices": {
            "debian": ["xeon", "gaudi"],
        },
        "default_device": "xeon",
        "offline_support": [],
        "ports": {
            "docker": {"rag": "9095"},
            "k8s_services": {"rag": "agentqna-ragagent"},
        },
        "test_connections": {
            "main_service": {
                "service_key": "rag",
                "path": "/v1/chat/completions",
                "method": "POST",
                "payload": {
                    "messages": [{"role": "user", "content": "Tell me about Michael Jackson song Thriller"}],
                    "max_new_tokens": 100,
                },
                "headers": {"Content-Type": "application/json"},
                "expect_code": 200,
            },
        },
        "interactive_params": {
            "xeon": [
                {
                    "name": "openai_api_key",
                    "prompt": "OpenAI API Key",
                    "type": str,
                    "default": "your-openai-api-key",
                    "help": "Required for Xeon deployment which uses OpenAI models.",
                    "required": True,
                }
            ],
            "gaudi": [
                {
                    "name": "llm_model",
                    "prompt": "LLM Model ID (for Gaudi)",
                    "type": str,
                    "help": "e.g., meta-llama/Meta-Llama-3-8B-Instruct",
                },
                {
                    "name": "num_shards",
                    "prompt": "Number of Gaudi HPU cards (shards)",
                    "type": int,
                    "help": "e.g., 1, 2, 4. Controls tensor parallel size.",
                },
            ],
        },
    },
}

# --- Deployment and Testing Configurations ---

# Time in seconds to wait after a deployment before starting connection tests
POST_DEPLOY_WAIT_S = int(os.getenv("POST_DEPLOY_WAIT_S", 120))

# Number of times to retry the connection test if it fails
TEST_RETRY_ATTEMPTS = int(os.getenv("TEST_RETRY_ATTEMPTS", 3))

# Time in seconds to wait between each connection test retry
TEST_RETRY_DELAY_S = 30

CLEANUP_ON_DEPLOY_FAILURE = False

# For CI TEST
K8S_VLLM_SKIP_WARMUP = os.getenv("OPEA_K8S_VLLM_SKIP_WARMUP", "false").lower() in ("true", "1", "t", "yes")
