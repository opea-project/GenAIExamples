# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import pathlib
import sys
from pathlib import Path

from fastapi import File, Form, HTTPException, UploadFile

cur_path = pathlib.Path(__file__).parent.resolve()
comps_path = os.path.join(cur_path, "../../../")
sys.path.append(comps_path)

from typing import List

from tqdm import tqdm

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.guardrails.pii_detection.data_utils import document_loader, parse_html
from comps.guardrails.pii_detection.pii.pii_utils import PIIDetector, PIIDetectorWithML, PIIDetectorWithNER
from comps.guardrails.pii_detection.ray_utils import ray_execute, ray_runner_initialization, rayds_initialization
from comps.guardrails.pii_detection.utils import (
    Timer,
    generate_log_name,
    get_max_cpus,
    prepare_env,
    save_file_to_local_disk,
)

logger = CustomLogger("guardrails-pii-detection")
logflag = os.getenv("LOGFLAG", False)


def get_pii_detection_inst(strategy="dummy", settings=None):
    if strategy == "ner":
        if logflag:
            logger.info("invoking NER detector.......")
        return PIIDetectorWithNER()
    elif strategy == "ml":
        if logflag:
            logger.info("invoking ML detector.......")
        return PIIDetectorWithML()
    else:
        raise ValueError(f"Invalid strategy: {strategy}")


def file_based_pii_detect(file_list: List[DocPath], strategy, enable_ray=False, debug=False):
    """Ingest document to Redis."""
    file_list = [f.path for f in file_list]
    pii_detector = get_pii_detection_inst(strategy=strategy)

    if enable_ray:
        num_cpus = get_max_cpus(len(file_list))
        if logflag:
            logger.info(f"per task num_cpus: {num_cpus}")

        log_name = generate_log_name(file_list)
        ds = rayds_initialization(file_list, document_loader, lazy_mode=True, num_cpus=num_cpus)
        ds = ds.map(ray_runner_initialization(pii_detector.detect_pii, debug=debug), num_cpus=num_cpus)
        ret = ray_execute(ds, log_name)

    else:
        ret = []
        for file in tqdm(file_list, total=len(file_list)):
            with Timer(f"read document {file}."):
                data = document_loader(file)
            with Timer(f"detect pii on document {file}"):
                ret.append(pii_detector.detect_pii(data))
    return ret


def link_based_pii_detect(link_list: List[str], strategy, enable_ray=False, debug=False):
    link_list = [str(f) for f in link_list]
    pii_detector = get_pii_detection_inst(strategy=strategy)

    def _parse_html(link):
        data = parse_html([link])
        return data[0][0]

    if enable_ray:
        num_cpus = get_max_cpus(len(link_list))
        if logflag:
            logger.info(f"per task num_cpus: {num_cpus}")

        log_name = generate_log_name(link_list)
        ds = rayds_initialization(link_list, _parse_html, lazy_mode=True, num_cpus=num_cpus)
        ds = ds.map(ray_runner_initialization(pii_detector.detect_pii, debug=debug), num_cpus=num_cpus)
        ret = ray_execute(ds, log_name)
    else:
        ret = []
        for link in tqdm(link_list, total=len(link_list)):
            with Timer(f"read document {link}."):
                data = _parse_html(link)
            if debug or logflag:
                logger.info("content is: ", data)
            with Timer(f"detect pii on document {link}"):
                ret.append(pii_detector.detect_pii(data))
    return ret


def text_based_pii_detect(text_list: List[str], strategy, enable_ray=False, debug=False):
    text_list = [str(f) for f in text_list]
    pii_detector = get_pii_detection_inst(strategy=strategy)

    if enable_ray:
        num_cpus = get_max_cpus(len(text_list))
        if logflag:
            logger.info(f"per task num_cpus: {num_cpus}")

        log_name = generate_log_name(text_list)
        ds = rayds_initialization(text_list, None, lazy_mode=True, num_cpus=num_cpus)
        ds = ds.map(ray_runner_initialization(pii_detector.detect_pii, debug=debug), num_cpus=num_cpus)
        ret = ray_execute(ds, log_name)
    else:
        ret = []
        for data in tqdm(text_list, total=len(text_list)):
            if debug or logflag:
                logger.info("content is: ", data)
            with Timer(f"detect pii on document {data[:50]}"):
                ret.append(pii_detector.detect_pii(data))
    return ret


@register_microservice(
    name="opea_service@guardrails-pii-detection", endpoint="/v1/piidetect", host="0.0.0.0", port=6357
)
async def pii_detection(
    files: List[UploadFile] = File(None),
    link_list: str = Form(None),
    text_list: str = Form(None),
    strategy: str = Form(None),
):
    if logflag:
        logger.info(files)
        logger.info(link_list)
        logger.info(text_list)
        logger.info(strategy)
    if not files and not link_list and not text_list:
        raise HTTPException(status_code=400, detail="Either files, link_list, or text_list must be provided.")

    if strategy is None:
        strategy = "ner"

    if logflag:
        logger.info("PII detection using strategy: ", strategy)

    pip_requirement = ["detect-secrets", "phonenumbers", "gibberish-detector"]

    if files:
        saved_path_list = []
        try:
            if not isinstance(files, list):
                files = [files]
            upload_folder = "./uploaded_files/"
            if not os.path.exists(upload_folder):
                Path(upload_folder).mkdir(parents=True, exist_ok=True)

            # TODO: use ray to parallelize the file saving
            for file in files:
                save_path = upload_folder + file.filename
                await save_file_to_local_disk(save_path, file)
                saved_path_list.append(DocPath(path=save_path))

            enable_ray = False if (len(text_list) <= 10 or strategy == "ml") else True
            if enable_ray:
                prepare_env(enable_ray=enable_ray, pip_requirements=pip_requirement, comps_path=comps_path)
            ret = file_based_pii_detect(saved_path_list, strategy, enable_ray=enable_ray)
            result = {"status": 200, "message": json.dumps(ret)}
            if logflag:
                logger.info(result)
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"An error occurred: {e}")

    if text_list:
        try:
            text_list = json.loads(text_list)  # Parse JSON string to list
            if not isinstance(text_list, list):
                text_list = [text_list]
            enable_ray = False if (len(text_list) <= 10 or strategy == "ml") else True
            if enable_ray:
                prepare_env(enable_ray=enable_ray, pip_requirements=pip_requirement, comps_path=comps_path)
            ret = text_based_pii_detect(text_list, strategy, enable_ray=enable_ray)
            result = {"status": 200, "message": json.dumps(ret)}
            if logflag:
                logger.info(result)
            return result
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"An error occurred: {e}")

    if link_list:
        try:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                link_list = [link_list]
            enable_ray = False if (len(text_list) <= 10 or strategy == "ml") else True
            if enable_ray:
                prepare_env(enable_ray=enable_ray, pip_requirements=pip_requirement, comps_path=comps_path)
            ret = link_based_pii_detect(link_list, strategy, enable_ray=enable_ray)
            result = {"status": 200, "message": json.dumps(ret)}
            if logflag:
                logger.info(result)
            return result
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


if __name__ == "__main__":
    opea_microservices["opea_service@guardrails-pii-detection"].start()
