# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type, Union

from config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, LVM_ENDPOINT, REDIS_URL, WHISPER_MODEL
from fastapi import File, HTTPException, UploadFile
from langchain_community.utilities.redis import _array_to_buffer
from langchain_community.vectorstores import Redis
from langchain_community.vectorstores.redis.base import _generate_field_schema, _prepare_metadata
from langchain_community.vectorstores.redis.schema import read_schema
from langchain_core.embeddings import Embeddings
from langchain_core.utils import get_from_dict_or_env
from PIL import Image

from comps import opea_microservices, register_microservice
from comps.dataprep.multimodal_utils import (
    clear_upload_folder,
    convert_video_to_audio,
    create_upload_folder,
    delete_audio_file,
    extract_frames_and_annotations_from_transcripts,
    extract_frames_and_generate_captions,
    extract_transcript_from_audio,
    generate_video_id,
    load_json_file,
    load_whisper_model,
    write_vtt,
)
from comps.embeddings.multimodal_embeddings.bridgetower.bridgetower_embedding import BridgeTowerEmbedding

device = "cpu"
upload_folder = "./uploaded_files/"


class MultimodalRedis(Redis):
    """Redis vector database to process multimodal data."""

    @classmethod
    def from_text_image_pairs_return_keys(
        cls: Type[Redis],
        texts: List[str],
        images: List[str],
        embedding: Embeddings = BridgeTowerEmbedding,
        metadatas: Optional[List[dict]] = None,
        index_name: Optional[str] = None,
        index_schema: Optional[Union[Dict[str, str], str, os.PathLike]] = None,
        vector_schema: Optional[Dict[str, Union[str, int]]] = None,
        **kwargs: Any,
    ):
        """
        Args:
            texts (List[str]): List of texts to add to the vectorstore.
            images (List[str]): List of path-to-images to add to the vectorstore.
            embedding (Embeddings): Embeddings to use for the vectorstore.
            metadatas (Optional[List[dict]], optional): Optional list of metadata
                dicts to add to the vectorstore. Defaults to None.
            index_name (Optional[str], optional): Optional name of the index to
                create or add to. Defaults to None.
            index_schema (Optional[Union[Dict[str, str], str, os.PathLike]], optional):
                Optional fields to index within the metadata. Overrides generated
                schema. Defaults to None.
            vector_schema (Optional[Dict[str, Union[str, int]]], optional): Optional
                vector schema to use. Defaults to None.
            **kwargs (Any): Additional keyword arguments to pass to the Redis client.
        Returns:
            Tuple[Redis, List[str]]: Tuple of the Redis instance and the keys of
                the newly created documents.
        Raises:
            ValueError: If the number of texts does not equal the number of images.
            ValueError: If the number of metadatas does not match the number of texts.
        """
        # the length of texts must be equal to the length of images
        if len(texts) != len(images):
            raise ValueError(f"the len of captions {len(texts)} does not equal the len of images {len(images)}")

        redis_url = get_from_dict_or_env(kwargs, "redis_url", "REDIS_URL")

        if "redis_url" in kwargs:
            kwargs.pop("redis_url")

        # flag to use generated schema
        if "generate" in kwargs:
            kwargs.pop("generate")

        # see if the user specified keys
        keys = None
        if "keys" in kwargs:
            keys = kwargs.pop("keys")

        # Name of the search index if not given
        if not index_name:
            index_name = uuid.uuid4().hex

        # type check for metadata
        if metadatas:
            if isinstance(metadatas, list) and len(metadatas) != len(texts):  # type: ignore  # noqa: E501
                raise ValueError("Number of metadatas must match number of texts")
            if not (isinstance(metadatas, list) and isinstance(metadatas[0], dict)):
                raise ValueError("Metadatas must be a list of dicts")
            generated_schema = _generate_field_schema(metadatas[0])

            if not index_schema:
                index_schema = generated_schema

        # Create instance
        instance = cls(
            redis_url,
            index_name,
            embedding,
            index_schema=index_schema,
            vector_schema=vector_schema,
            **kwargs,
        )
        # Add data to Redis
        keys = instance.add_text_image_pairs(texts, images, metadatas, keys=keys)
        return instance, keys

    def add_text_image_pairs(
        self,
        texts: Iterable[str],
        images: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        embeddings: Optional[List[List[float]]] = None,
        batch_size: int = 2,
        clean_metadata: bool = True,
        **kwargs: Any,
    ) -> List[str]:
        """Add more embeddings of text-image pairs to the vectorstore.

        Args:
            texts (Iterable[str]): Iterable of strings/text to add to the vectorstore.
            images: Iterable[str]: Iterable of strings/text of path-to-image to add to the vectorstore.
            metadatas (Optional[List[dict]], optional): Optional list of metadatas.
                Defaults to None.
            embeddings (Optional[List[List[float]]], optional): Optional pre-generated
                embeddings. Defaults to None.
            keys (List[str]) or ids (List[str]): Identifiers of entries.
                Defaults to None.
            batch_size (int, optional): Batch size to use for writes. Defaults to 1000.
        Returns:
            List[str]: List of ids added to the vectorstore
        """
        ids = []
        # Get keys or ids from kwargs
        # Other vectorstores use ids
        keys_or_ids = kwargs.get("keys", kwargs.get("ids"))

        # type check for metadata
        if metadatas:
            if isinstance(metadatas, list) and len(metadatas) != len(texts):  # type: ignore  # noqa: E501
                raise ValueError("Number of metadatas must match number of texts")
            if not (isinstance(metadatas, list) and isinstance(metadatas[0], dict)):
                raise ValueError("Metadatas must be a list of dicts")
        pil_imgs = [Image.open(img) for img in images]
        if not embeddings:
            embeddings = self._embeddings.embed_image_text_pairs(list(texts), pil_imgs, batch_size=batch_size)
        self._create_index_if_not_exist(dim=len(embeddings[0]))

        # Write data to redis
        pipeline = self.client.pipeline(transaction=False)
        for i, text in enumerate(texts):
            # Use provided values by default or fallback
            key = keys_or_ids[i] if keys_or_ids else str(uuid.uuid4().hex)
            if not key.startswith(self.key_prefix + ":"):
                key = self.key_prefix + ":" + key
            metadata = metadatas[i] if metadatas else {}
            metadata = _prepare_metadata(metadata) if clean_metadata else metadata
            pipeline.hset(
                key,
                mapping={
                    self._schema.content_key: text,
                    self._schema.content_vector_key: _array_to_buffer(embeddings[i], self._schema.vector_dtype),
                    **metadata,
                },
            )
            ids.append(key)

            # Write batch
            if i % batch_size == 0:
                pipeline.execute()

        # Cleanup final batch
        pipeline.execute()
        return ids


def prepare_data_and_metadata_from_annotation(
    annotation, path_to_frames, title, num_transcript_concat_for_ingesting=2, num_transcript_concat_for_inference=7
):
    text_list = []
    image_list = []
    metadatas = []
    for i, frame in enumerate(annotation):
        frame_index = frame["sub_video_id"]
        path_to_frame = os.path.join(path_to_frames, f"frame_{frame_index}.jpg")
        # augment this frame's transcript with a reasonable number of neighboring frames' transcripts helps semantic retrieval
        lb_ingesting = max(0, i - num_transcript_concat_for_ingesting)
        ub_ingesting = min(len(annotation), i + num_transcript_concat_for_ingesting + 1)
        caption_for_ingesting = " ".join([annotation[j]["caption"] for j in range(lb_ingesting, ub_ingesting)])

        # augment this frame's transcript with more neighboring frames' transcript to provide more context to LVM for question answering
        lb_inference = max(0, i - num_transcript_concat_for_inference)
        ub_inference = min(len(annotation), i + num_transcript_concat_for_inference + 1)
        caption_for_inference = " ".join([annotation[j]["caption"] for j in range(lb_inference, ub_inference)])

        video_id = frame["video_id"]
        b64_img_str = frame["b64_img_str"]
        time_of_frame = frame["time"]
        embedding_type = "pair"
        source_video = frame["video_name"]

        text_list.append(caption_for_ingesting)
        image_list.append(path_to_frame)
        metadatas.append(
            {
                "content": caption_for_ingesting,
                "b64_img_str": b64_img_str,
                "video_id": video_id,
                "source_video": source_video,
                "time_of_frame_ms": float(time_of_frame),
                "embedding_type": embedding_type,
                "title": title,
                "transcript_for_inference": caption_for_inference,
            }
        )

    return text_list, image_list, metadatas


def ingest_multimodal(videoname, data_folder, embeddings):
    """Ingest text image pairs to Redis from the data/ directory that consists of frames and annotations."""
    data_folder = os.path.abspath(data_folder)
    annotation_file_path = os.path.join(data_folder, "annotations.json")
    path_to_frames = os.path.join(data_folder, "frames")

    annotation = load_json_file(annotation_file_path)

    # prepare data to ingest
    text_list, image_list, metadatas = prepare_data_and_metadata_from_annotation(annotation, path_to_frames, videoname)

    MultimodalRedis.from_text_image_pairs_return_keys(
        texts=[f"From {videoname}. " + text for text in text_list],
        images=image_list,
        embedding=embeddings,
        metadatas=metadatas,
        index_name=INDEX_NAME,
        index_schema=INDEX_SCHEMA,
        redis_url=REDIS_URL,
    )


def drop_index(index_name, redis_url=REDIS_URL):
    print(f"dropping index {index_name}")
    try:
        assert Redis.drop_index(index_name=index_name, delete_documents=True, redis_url=redis_url)
        print(f"index {index_name} deleted")
    except Exception as e:
        print(f"index {index_name} delete failed: {e}")
        return False
    return True


@register_microservice(
    name="opea_service@prepare_videodoc_redis", endpoint="/v1/generate_transcripts", host="0.0.0.0", port=6007
)
async def ingest_videos_generate_transcripts(files: List[UploadFile] = File(None)):
    """Upload videos with speech, generate transcripts using whisper and ingest into redis."""

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
            st = time.time()
            print(f"Processing video {video_file.filename}")

            # Assign unique identifier to video
            video_id = generate_video_id()

            # Create video file name by appending identifier
            video_name = os.path.splitext(video_file.filename)[0]
            video_file_name = f"{video_name}_{video_id}.mp4"
            video_dir_name = os.path.splitext(video_file_name)[0]

            # Save video file in upload_directory
            with open(os.path.join(upload_folder, video_file_name), "wb") as f:
                shutil.copyfileobj(video_file.file, f)

            # Extract temporary audio wav file from video mp4
            audio_file = video_dir_name + ".wav"
            print(f"Extracting {audio_file}")
            convert_video_to_audio(
                os.path.join(upload_folder, video_file_name), os.path.join(upload_folder, audio_file)
            )
            print(f"Done extracting {audio_file}")

            # Load whisper model
            print("Loading whisper model....")
            whisper_model = load_whisper_model(model_name=WHISPER_MODEL)
            print("Done loading whisper!")

            # Extract transcript from audio
            print("Extracting transcript from audio")
            transcripts = extract_transcript_from_audio(whisper_model, os.path.join(upload_folder, audio_file))

            # Save transcript as vtt file and delete audio file
            vtt_file = video_dir_name + ".vtt"
            write_vtt(transcripts, os.path.join(upload_folder, vtt_file))
            delete_audio_file(os.path.join(upload_folder, audio_file))
            print("Done extracting transcript.")

            # Store frames and caption annotations in a new directory
            print("Extracting frames and generating annotation")
            extract_frames_and_annotations_from_transcripts(
                video_id,
                os.path.join(upload_folder, video_file_name),
                os.path.join(upload_folder, vtt_file),
                os.path.join(upload_folder, video_dir_name),
            )
            print("Done extracting frames and generating annotation")
            # Delete temporary vtt file
            os.remove(os.path.join(upload_folder, vtt_file))

            # Ingest multimodal data into redis
            print("Ingesting data to redis vector store")
            ingest_multimodal(video_name, os.path.join(upload_folder, video_dir_name), embeddings)

            # Delete temporary video directory containing frames and annotations
            shutil.rmtree(os.path.join(upload_folder, video_dir_name))

            print(f"Processed video {video_file.filename}")
            end = time.time()
            print(str(end - st))

        return {"status": 200, "message": "Data preparation succeeded"}

    raise HTTPException(status_code=400, detail="Must provide at least one video (.mp4) file.")


@register_microservice(
    name="opea_service@prepare_videodoc_redis", endpoint="/v1/generate_captions", host="0.0.0.0", port=6007
)
async def ingest_videos_generate_caption(files: List[UploadFile] = File(None)):
    """Upload videos without speech (only background music or no audio), generate captions using lvm microservice and ingest into redis."""

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
            print(f"Processing video {video_file.filename}")

            # Assign unique identifier to video
            video_id = generate_video_id()

            # Create video file name by appending identifier
            video_name = os.path.splitext(video_file.filename)[0]
            video_file_name = f"{video_name}_{video_id}.mp4"
            video_dir_name = os.path.splitext(video_file_name)[0]

            # Save video file in upload_directory
            with open(os.path.join(upload_folder, video_file_name), "wb") as f:
                shutil.copyfileobj(video_file.file, f)

            # Store frames and caption annotations in a new directory
            extract_frames_and_generate_captions(
                video_id,
                os.path.join(upload_folder, video_file_name),
                LVM_ENDPOINT,
                os.path.join(upload_folder, video_dir_name),
            )

            # Ingest multimodal data into redis
            ingest_multimodal(video_name, os.path.join(upload_folder, video_dir_name), embeddings)

            # Delete temporary video directory containing frames and annotations
            # shutil.rmtree(os.path.join(upload_folder, video_dir_name))

            print(f"Processed video {video_file.filename}")

        return {"status": 200, "message": "Data preparation succeeded"}

    raise HTTPException(status_code=400, detail="Must provide at least one video (.mp4) file.")


@register_microservice(
    name="opea_service@prepare_videodoc_redis",
    endpoint="/v1/videos_with_transcripts",
    host="0.0.0.0",
    port=6007,
)
async def ingest_videos_with_transcripts(files: List[UploadFile] = File(None)):

    if files:
        video_files, video_file_names = [], []
        captions_files, captions_file_names = [], []
        for file in files:
            if os.path.splitext(file.filename)[1] == ".mp4":
                video_files.append(file)
                video_file_names.append(file.filename)
            elif os.path.splitext(file.filename)[1] == ".vtt":
                captions_files.append(file)
                captions_file_names.append(file.filename)
            else:
                print(f"Skipping file {file.filename} because of unsupported format.")

        # Check if every video file has a captions file
        for video_file_name in video_file_names:
            file_prefix = os.path.splitext(video_file_name)[0]
            if (file_prefix + ".vtt") not in captions_file_names:
                raise HTTPException(
                    status_code=400, detail=f"No captions file {file_prefix}.vtt found for {video_file_name}"
                )

        if len(video_files) == 0:
            return HTTPException(
                status_code=400,
                detail="The uploaded files have unsupported formats. Please upload at least one video file (.mp4) with captions (.vtt)",
            )

        for video_file in video_files:
            print(f"Processing video {video_file.filename}")

            # Assign unique identifier to video
            video_id = generate_video_id()

            # Create video file name by appending identifier
            video_name = os.path.splitext(video_file.filename)[0]
            video_file_name = f"{video_name}_{video_id}.mp4"
            video_dir_name = os.path.splitext(video_file_name)[0]

            # Save video file in upload_directory
            with open(os.path.join(upload_folder, video_file_name), "wb") as f:
                shutil.copyfileobj(video_file.file, f)

            # Save captions file in upload directory
            vtt_file_name = os.path.splitext(video_file.filename)[0] + ".vtt"
            vtt_idx = None
            for idx, caption_file in enumerate(captions_files):
                if caption_file.filename == vtt_file_name:
                    vtt_idx = idx
                    break
            vtt_file = video_dir_name + ".vtt"
            with open(os.path.join(upload_folder, vtt_file), "wb") as f:
                shutil.copyfileobj(captions_files[vtt_idx].file, f)

            # Store frames and caption annotations in a new directory
            extract_frames_and_annotations_from_transcripts(
                video_id,
                os.path.join(upload_folder, video_file_name),
                os.path.join(upload_folder, vtt_file),
                os.path.join(upload_folder, video_dir_name),
            )

            # Delete temporary vtt file
            os.remove(os.path.join(upload_folder, vtt_file))

            # Ingest multimodal data into redis
            ingest_multimodal(video_name, os.path.join(upload_folder, video_dir_name), embeddings)

            # Delete temporary video directory containing frames and annotations
            shutil.rmtree(os.path.join(upload_folder, video_dir_name))

            print(f"Processed video {video_file.filename}")

        return {"status": 200, "message": "Data preparation succeeded"}

    raise HTTPException(
        status_code=400, detail="Must provide at least one pair consisting of video (.mp4) and captions (.vtt)"
    )


@register_microservice(
    name="opea_service@prepare_videodoc_redis", endpoint="/v1/dataprep/get_videos", host="0.0.0.0", port=6007
)
async def rag_get_file_structure():
    """Returns list of names of uploaded videos saved on the server."""

    if not Path(upload_folder).exists():
        print("No file uploaded, return empty list.")
        return []

    uploaded_videos = os.listdir(upload_folder)
    return uploaded_videos


@register_microservice(
    name="opea_service@prepare_videodoc_redis", endpoint="/v1/dataprep/delete_videos", host="0.0.0.0", port=6007
)
async def delete_videos():
    """Delete all uploaded videos along with redis index."""
    index_deleted = drop_index(index_name=INDEX_NAME)

    if not index_deleted:
        raise HTTPException(status_code=409, detail="Uploaded videos could not be deleted. Index does not exist")

    clear_upload_folder(upload_folder)
    print("Successfully deleted all uploaded videos.")
    return {"status": True}


if __name__ == "__main__":
    create_upload_folder(upload_folder)
    # Load embeddings model
    print("Initializing BridgeTower model as embedder...")
    embeddings = BridgeTowerEmbedding(model_name=EMBED_MODEL, device=device)
    print("Done initialization of embedder!")
    opea_microservices["opea_service@prepare_videodoc_redis"].start()
