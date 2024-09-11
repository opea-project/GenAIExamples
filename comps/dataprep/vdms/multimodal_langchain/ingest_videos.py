# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type, Union

from fastapi import File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from tqdm import tqdm
from utils import store_embeddings
from utils.utils import process_all_videos, read_config
from utils.vclip import vCLIP

from comps import opea_microservices, register_microservice

VECTORDB_SERVICE_HOST_IP = os.getenv("VDMS_HOST", "0.0.0.0")
VECTORDB_SERVICE_PORT = os.getenv("VDMS_PORT", 55555)
collection_name = os.getenv("INDEX_NAME", "rag-vdms")


def setup_vclip_model(config, device="cpu"):
    model = vCLIP(config)
    return model


def read_json(path):
    with open(path) as f:
        x = json.load(f)
    return x


def store_into_vectordb(vs, metadata_file_path, dimensions):
    GMetadata = read_json(metadata_file_path)

    total_videos = len(GMetadata.keys())

    for idx, (video, data) in enumerate(tqdm(GMetadata.items())):
        metadata_list = []
        ids = []

        data["video"] = video
        video_name_list = [data["video_path"]]
        metadata_list = [data]
        if vs.selected_db == "vdms":
            vs.video_db.add_videos(
                paths=video_name_list,
                metadatas=metadata_list,
                start_time=[data["timestamp"]],
                clip_duration=[data["clip_duration"]],
            )
        else:
            print(f"ERROR: selected_db {vs.selected_db} not supported. Supported:[vdms]")

    # clean up tmp_ folders containing frames (jpeg)
    for i in os.listdir():
        if i.startswith("tmp_"):
            print("removing tmp_*")
            os.system("rm -r tmp_*")
            break


def generate_video_id():
    """Generates a unique identifier for a video file."""
    return str(uuid.uuid4())


def generate_embeddings(config, dimensions, vs):
    process_all_videos(config)
    global_metadata_file_path = os.path.join(config["meta_output_dir"], "metadata.json")
    print(f"global metadata file available at {global_metadata_file_path}")
    store_into_vectordb(vs, global_metadata_file_path, dimensions)


@register_microservice(name="opea_service@prepare_videodoc_vdms", endpoint="/v1/dataprep", host="0.0.0.0", port=6007)
async def process_videos(files: List[UploadFile] = File(None)):
    """Ingest videos to VDMS."""

    config = read_config("./config.yaml")
    meanclip_cfg = {
        "model_name": config["embeddings"]["vclip_model_name"],
        "num_frm": config["embeddings"]["vclip_num_frm"],
    }
    generate_frames = config["generate_frames"]
    path = config["videos"]
    meta_output_dir = config["meta_output_dir"]
    emb_path = config["embeddings"]["path"]
    host = VECTORDB_SERVICE_HOST_IP
    port = int(VECTORDB_SERVICE_PORT)
    selected_db = config["vector_db"]["choice_of_db"]
    vector_dimensions = config["embeddings"]["vector_dimensions"]
    print(f"Parsing videos {path}.")

    # Saving videos
    if files:
        video_files = []
        for file in files:
            if os.path.splitext(file.filename)[1] == ".mp4":
                video_files.append(file)
            else:
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} is not an mp4 file. Please upload mp4 files only."
                )

        for video_file in video_files:
            video_id = generate_video_id()
            video_name = os.path.splitext(video_file.filename)[0]
            video_file_name = f"{video_name}_{video_id}.mp4"
            video_dir_name = os.path.splitext(video_file_name)[0]
            # Save video file in upload_directory
            with open(os.path.join(path, video_file_name), "wb") as f:
                shutil.copyfileobj(video_file.file, f)

    # Creating DB
    print(
        "Creating DB with video embedding and metadata support, \nIt may take few minutes to download and load all required models if you are running for first time.",
        flush=True,
    )
    print("Connecting to {} at {}:{}".format(selected_db, host, port), flush=True)

    # init meanclip model
    model = setup_vclip_model(meanclip_cfg, device="cpu")
    vs = store_embeddings.VideoVS(
        host, port, selected_db, model, collection_name, embedding_dimensions=vector_dimensions
    )
    print("done creating DB, sleep 5s", flush=True)
    time.sleep(5)

    generate_embeddings(config, vector_dimensions, vs)

    return {"message": "Videos ingested successfully"}


@register_microservice(
    name="opea_service@prepare_videodoc_vdms",
    endpoint="/v1/dataprep/get_videos",
    host="0.0.0.0",
    port=6007,
    methods=["GET"],
)
async def rag_get_file_structure():
    """Returns list of names of uploaded videos saved on the server."""
    config = read_config("./config.yaml")
    if not Path(config["videos"]).exists():
        print("No file uploaded, return empty list.")
        return []

    uploaded_videos = os.listdir(config["videos"])
    mp4_files = [file for file in uploaded_videos if file.endswith(".mp4")]
    return mp4_files


@register_microservice(
    name="opea_service@prepare_videodoc_vdms",
    endpoint="/v1/dataprep/get_file/{filename}",
    host="0.0.0.0",
    port=6007,
    methods=["GET"],
)
async def rag_get_file(filename: str):
    """Download the file from remote."""

    config = read_config("./config.yaml")
    UPLOAD_DIR = config["videos"]
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        return {"error": "File not found"}


if __name__ == "__main__":
    opea_microservices["opea_service@prepare_videodoc_vdms"].start()
