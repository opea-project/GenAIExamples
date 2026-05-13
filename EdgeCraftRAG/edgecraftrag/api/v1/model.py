# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import gc
import os
from typing import List, Optional
from urllib.parse import urlparse

import requests
from edgecraftrag.api_schema import ModelIn
from edgecraftrag.context import ctx
from fastapi import FastAPI, HTTPException, Query, status

model_app = FastAPI()

# Model path in container is set to '/home/user/models'
CONTAINER_MODEL_PATH = "/home/user/models/"


def _get_model_roots() -> List[str]:
    roots = []
    env_model_path = os.getenv("MODEL_PATH")
    candidates = [
        env_model_path,
        CONTAINER_MODEL_PATH,
        os.path.join(os.getcwd(), "models"),
        os.path.join(os.getcwd(), "../models"),
        os.path.join(os.path.dirname(__file__), "../../../models"),
        os.path.join(os.path.dirname(__file__), "../../../../models"),
    ]

    for candidate in candidates:
        if not candidate:
            continue
        resolved = os.path.realpath(os.path.normpath(os.path.expanduser(candidate)))
        if os.path.isdir(resolved) and resolved not in roots:
            roots.append(resolved)

    return roots


def _resolve_model_path(model_id: str) -> str:
    for root in _get_model_roots():
        requested_path = os.path.realpath(os.path.normpath(os.path.join(root, model_id)))
        if requested_path.startswith(root + os.sep) and os.path.exists(requested_path):
            weights = get_available_weights(requested_path)
            if len(weights) > 0:
                return requested_path

    for root in _get_model_roots():
        requested_path = os.path.realpath(os.path.normpath(os.path.join(root, model_id)))
        if requested_path.startswith(root + os.sep):
            return requested_path

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid model path")


# Search available model weight
@model_app.get(path="/v1/settings/weight/{model_id:path}")
async def get_model_weight(model_id):
    try:
        requested_path = _resolve_model_path(model_id)
        return get_available_weights(requested_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=" GET model weight failed")


# Search available model id
@model_app.get(path="/v1/settings/avail-models/{model_type}")
async def get_model_id(
    model_type: str,
    server_address: Optional[str] = Query(default=None, description="remote inference server address (optional)"),
):
    try:
        normalized_type = (model_type or "").strip().lower()

        if normalized_type == "vllm":
            return get_available_vllm_models(_normalize_server_address(server_address, "http://localhost:8086"))
        elif normalized_type == "ovms":
            return get_available_ovms_models(_normalize_server_address(server_address, "http://localhost:8000"))
        elif normalized_type == "vllm_embedding":
            return get_available_vllm_models(_normalize_server_address(server_address, "http://localhost:8087"))
        else:
            return get_available_models(model_type)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=" GET model failed",
        )


# GET Models
@model_app.get(path="/v1/settings/models")
async def get_models():
    return ctx.get_model_mgr().get_models()


# GET Model
@model_app.get(path="/v1/settings/models/{model_id:path}")
async def get_model_by_name(model_id):
    return ctx.get_model_mgr().get_model_by_name(model_id)


# POST Model
@model_app.post(path="/v1/settings/models")
async def add_model(request: ModelIn):
    modelmgr = ctx.get_model_mgr()
    # Currently use asyncio.Lock() to deal with multi-requests
    async with modelmgr._lock:
        model = modelmgr.search_model(request)
        if model is None:
            model = modelmgr.load_model(request)
            modelmgr.add(model)
    return model.model_id + " model loaded"


# PATCH Model
@model_app.patch(path="/v1/settings/models/{model_id:path}")
async def update_model(model_id, request: ModelIn):
    # The process of patch model is : 1.delete model 2.create model
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    modelmgr = ctx.get_model_mgr()
    if active_pl and active_pl.model_existed(model_id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Model is being used by active pipeline, unable to update"
        )
    else:
        async with modelmgr._lock:
            if modelmgr.get_model_by_name(model_id) is None:
                # Need to make sure original model still exists before updating model
                # to prevent memory leak in concurrent requests situation
                err_msg = "Model " + model_id + " not exists"
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
            model = modelmgr.search_model(request)
            if model is None:
                modelmgr.del_model_by_name(model_id)
                # Clean up memory occupation
                gc.collect()
                # load new model
                model = modelmgr.load_model(request)
                modelmgr.add(model)
        return model


# DELETE Model
@model_app.delete(path="/v1/settings/models/{model_id:path}")
async def delete_model(model_id):
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if active_pl and active_pl.model_existed(model_id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Model is being used by active pipeline, unable to remove"
        )
    else:
        modelmgr = ctx.get_model_mgr()
        # Currently use asyncio.Lock() to deal with multi-requests
        async with modelmgr._lock:
            response = modelmgr.del_model_by_name(model_id)
            # Clean up memory occupation
            gc.collect()
        return response


def get_available_weights(model_path):
    avail_weights_compression = set()

    model_name = os.path.basename(model_path).upper()
    if "INT4" in model_name:
        avail_weights_compression.add("INT4")
    if "INT8" in model_name:
        avail_weights_compression.add("INT8")
    if "FP16" in model_name:
        avail_weights_compression.add("FP16")

    for _, dirs, _ in os.walk(model_path):
        for dir_name in dirs:
            upper_name = dir_name.upper()
            if "INT4" in upper_name:
                avail_weights_compression.add("INT4")
            if "INT8" in upper_name:
                avail_weights_compression.add("INT8")
            if "FP16" in upper_name:
                avail_weights_compression.add("FP16")

    return [weight for weight in ["INT4", "INT8", "FP16"] if weight in avail_weights_compression]


def get_available_models(model_type):
    avail_models = []
    seen_models = set()
    model_roots = _get_model_roots()
    if not model_roots:
        model_roots = [os.path.realpath(os.path.normpath(CONTAINER_MODEL_PATH))]

    normalized_model_type = (model_type or "").strip().lower()

    def _is_llm_model_dir(file_names: set) -> bool:
        if "openvino_model.xml" in file_names and any(
            name.endswith(".bin") for name in file_names
        ):
            return True

        if "config.json" in file_names and (
            "pytorch_model.bin" in file_names
            or "model.safetensors" in file_names
            or any(name.endswith(".safetensors") for name in file_names)
            or "openvino_model.xml" in file_names
        ):
            return True

        if any(name.endswith(".gguf") for name in file_names):
            return True

        return False

    def _discover_llm_model_ids(model_root: str, max_depth: int = 6) -> List[str]:
        results: List[str] = []

        root = os.path.realpath(os.path.normpath(os.path.expanduser(model_root)))
        if not os.path.isdir(root):
            return results

        stack: List[tuple[str, str, int]] = [(root, "", 0)]
        while stack:
            abs_dir, rel_dir, depth = stack.pop()

            try:
                entries = list(os.scandir(abs_dir))
            except OSError:
                continue

            file_names = {e.name for e in entries if e.is_file(follow_symlinks=False)}
            if rel_dir and _is_llm_model_dir(file_names):
                results.append(rel_dir)
                continue

            if depth >= max_depth:
                continue

            subdirs = [e for e in entries if e.is_dir(follow_symlinks=False)]
            subdirs.sort(key=lambda e: e.name.lower(), reverse=True)
            for entry in subdirs:
                name = entry.name
                if not name or name.startswith("."):
                    continue
                if name == "BAAI" or (rel_dir and rel_dir.split("/", 1)[0] == "BAAI"):
                    continue
                if name in {"__pycache__", ".ov_cache", "ov_cache", "cache", "tmp"}:
                    continue

                next_rel = f"{rel_dir}/{name}" if rel_dir else name
                if next_rel.split("/", 1)[0] == "BAAI":
                    continue
                stack.append((entry.path, next_rel, depth + 1))

        return list(dict.fromkeys(results))

    def add_model(model_name: str):
        if model_name not in seen_models:
            seen_models.add(model_name)
            avail_models.append(model_name)

    if normalized_model_type == "vllm":
        LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B")
        add_model(LLM_MODEL)
    elif normalized_model_type == "llm":
        llm_candidates: List[str] = []
        for model_root in model_roots:
            llm_candidates.extend(_discover_llm_model_ids(model_root))

        for model_id in sorted(dict.fromkeys(llm_candidates), key=lambda s: s.lower()):
            add_model(model_id)
    elif normalized_model_type == "kbadmin_embedding_model":
        return ["BAAI/bge-large-zh-v1.5"]
    else:
        for model_root in model_roots:
            baai_dir = os.path.join(model_root, "BAAI")
            if not os.path.isdir(baai_dir):
                continue
            for item in os.listdir(baai_dir):
                if (normalized_model_type == "reranker" and "rerank" in item) or (
                    normalized_model_type == "embedding" and "rerank" not in item
                ):
                    add_model("BAAI/" + item)

    return avail_models


@model_app.get(path="/v1/available_models")
def get_available_vllm_models(server_address: str):
    try:
        base_url = _normalize_server_address(server_address, "http://localhost:8086")
        url = f"{base_url}/v1/models"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return _extract_model_ids(response.json())

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to vLLM server: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


def _normalize_server_address(server_address: Optional[str], default: str) -> str:
    address = (server_address or "").strip() or default
    if not address.startswith(("http://", "https://")):
        address = f"http://{address}"

    parsed = urlparse(address)
    base = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else address
    path = (parsed.path or "").rstrip("/")

    # Accept inputs like http://host:port/v1 and normalize back to base host.
    if path and path != "/v1":
        base = f"{base}{path}"

    return base.rstrip("/")


def _extract_model_ids(response_data) -> List[str]:
    models = []

    if isinstance(response_data, dict):
        data = response_data.get("data")
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and entry.get("id"):
                    models.append(entry["id"])

        items = response_data.get("models")
        if isinstance(items, list):
            for entry in items:
                if isinstance(entry, dict):
                    model_name = entry.get("name") or entry.get("id")
                    if model_name:
                        models.append(model_name)

        config = response_data.get("config")
        if isinstance(config, dict):
            models.extend(config.keys())

        if not models:
            # Some OVMS APIs return a model-name keyed dict at top level.
            for key, value in response_data.items():
                if isinstance(value, dict) and ("base_path" in value or "model_version_policy" in value):
                    models.append(key)

    # Keep original order while deduplicating.
    return list(dict.fromkeys(models))


def _extract_ovms_model_names(response_data) -> List[str]:
    models: List[str] = []
    try:
        models.extend(_extract_model_ids(response_data))
    except Exception:
        pass

    if isinstance(response_data, dict):
        model_config_list = response_data.get("model_config_list")
        if isinstance(model_config_list, list):
            for entry in model_config_list:
                if isinstance(entry, dict) and entry.get("name"):
                    models.append(entry["name"])

        for key, value in response_data.items():
            if not isinstance(key, str):
                continue
            if not isinstance(value, dict):
                continue
            if "model_version_status" in value and isinstance(value.get("model_version_status"), list):
                models.append(key)
                continue

            if any(field in value for field in ("base_path", "model_version_policy", "state")):
                models.append(key)
    if isinstance(response_data, list):
        for entry in response_data:
            if isinstance(entry, dict):
                name = entry.get("name") or entry.get("id")
                if name:
                    models.append(name)
            elif isinstance(entry, str):
                models.append(entry)

    return list(dict.fromkeys([m for m in models if isinstance(m, str) and m.strip()]))


def get_available_ovms_models(server_address: str) -> List[str]:
    base_url = _normalize_server_address(server_address, "http://localhost:8000")
    errors = []

    for endpoint in ("/v1/models", "/v1/config", "/v2/models"):
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            models = _extract_ovms_model_names(response.json())
            if models:
                return models
        except Exception as exc:
            errors.append(f"{endpoint}: {exc}")

    # Fall back to configured/default model name to keep generator setup usable.
    fallback_model = os.getenv("OVMS_MODEL_NAME") or os.getenv("LLM_MODEL")
    if fallback_model:
        return [fallback_model]

    detail = "Failed to discover OVMS models"
    if errors:
        detail += f" ({'; '.join(errors)})"
    raise HTTPException(status_code=500, detail=detail)
