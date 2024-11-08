# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type, Union

from config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, LVM_ENDPOINT, REDIS_URL, WHISPER_MODEL
from fastapi import File, HTTPException, UploadFile
from langchain_community.utilities.redis import _array_to_buffer
from langchain_community.vectorstores import Redis
from langchain_community.vectorstores.redis.base import _generate_field_schema, _prepare_metadata
from langchain_core.embeddings import Embeddings
from langchain_core.utils import get_from_dict_or_env
from multimodal_utils import (
    clear_upload_folder,
    convert_video_to_audio,
    create_upload_folder,
    delete_audio_file,
    extract_frames_and_annotations_from_transcripts,
    extract_frames_and_generate_captions,
    extract_transcript_from_audio,
    generate_annotations_from_transcript,
    generate_id,
    load_json_file,
    load_whisper_model,
    write_vtt,
)
from PIL import Image

from comps import opea_microservices, register_microservice
from comps.embeddings.multimodal.bridgetower.bridgetower_embedding import BridgeTowerEmbedding

device = "cpu"
upload_folder = "./uploaded_files/"


class MultimodalRedis(Redis):
    """Redis vector database to process multimodal data."""

    @classmethod
    def from_text_image_pairs_return_keys(
        cls: Type[Redis],
        texts: List[str],
        images: List[str] = None,
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
            images (List[str]): Optional list of path-to-images to add to the vectorstore. If provided, the length of
                the list of images must match the length of the list of text strings.
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
        # If images are provided, the length of texts must be equal to the length of images
        if images and len(texts) != len(images):
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
        keys = (
            instance.add_text_image_pairs(texts, images, metadatas, keys=keys)
            if images
            else instance.add_text(texts, metadatas, keys=keys)
        )
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

    def add_text(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        embeddings: Optional[List[List[float]]] = None,
        clean_metadata: bool = True,
        **kwargs: Any,
    ) -> List[str]:
        """Add more embeddings of text to the vectorstore.

        Args:
            texts (Iterable[str]): Iterable of strings/text to add to the vectorstore.
            metadatas (Optional[List[dict]], optional): Optional list of metadatas.
                Defaults to None.
            embeddings (Optional[List[List[float]]], optional): Optional pre-generated
                embeddings. Defaults to None.
            keys (List[str]) or ids (List[str]): Identifiers of entries.
                Defaults to None.
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

        if not embeddings:
            embeddings = self._embeddings.embed_documents(list(texts))
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
        path_to_frame = os.path.join(path_to_frames, f"frame_{frame_index}.png")
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
        embedding_type = "pair" if b64_img_str else "text"
        source_video = frame["video_name"]

        text_list.append(caption_for_ingesting)

        if b64_img_str:
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
async def ingest_generate_transcripts(files: List[UploadFile] = File(None)):
    """Upload videos or audio files with speech, generate transcripts using whisper and ingest into redis."""

    if files:
        files_to_ingest = []
        uploaded_files_map = {}
        for file in files:
            if os.path.splitext(file.filename)[1] in [".mp4", ".wav"]:
                files_to_ingest.append(file)
            else:
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} is not an mp4 file. Please upload mp4 files only."
                )

        for file_to_ingest in files_to_ingest:
            st = time.time()
            file_extension = os.path.splitext(file_to_ingest.filename)[1]
            is_video = file_extension == ".mp4"
            file_type_str = "video" if is_video else "audio file"
            print(f"Processing {file_type_str} {file_to_ingest.filename}")

            # Assign unique identifier to video
            file_id = generate_id()

            # Create video file name by appending identifier
            base_file_name = os.path.splitext(file_to_ingest.filename)[0]
            file_name_with_id = f"{base_file_name}_{file_id}{file_extension}"
            dir_name = os.path.splitext(file_name_with_id)[0]

            # Save file in upload_directory
            with open(os.path.join(upload_folder, file_name_with_id), "wb") as f:
                shutil.copyfileobj(file_to_ingest.file, f)

            uploaded_files_map[base_file_name] = file_name_with_id

            if is_video:
                # Extract temporary audio wav file from video mp4
                audio_file = dir_name + ".wav"
                print(f"Extracting {audio_file}")
                convert_video_to_audio(
                    os.path.join(upload_folder, file_name_with_id), os.path.join(upload_folder, audio_file)
                )
                print(f"Done extracting {audio_file}")
            else:
                # We already have an audio file
                audio_file = file_name_with_id

            # Load whisper model
            print("Loading whisper model....")
            whisper_model = load_whisper_model(model_name=WHISPER_MODEL)
            print("Done loading whisper!")

            # Extract transcript from audio
            print("Extracting transcript from audio")
            transcripts = extract_transcript_from_audio(whisper_model, os.path.join(upload_folder, audio_file))

            # Save transcript as vtt file and delete audio file
            vtt_file = dir_name + ".vtt"
            write_vtt(transcripts, os.path.join(upload_folder, vtt_file))
            if is_video:
                delete_audio_file(os.path.join(upload_folder, audio_file))
            print("Done extracting transcript.")

            if is_video:
                # Store frames and caption annotations in a new directory
                print("Extracting frames and generating annotation")
                extract_frames_and_annotations_from_transcripts(
                    file_id,
                    os.path.join(upload_folder, file_name_with_id),
                    os.path.join(upload_folder, vtt_file),
                    os.path.join(upload_folder, dir_name),
                )
            else:
                # Generate annotations based on the transcript
                print("Generating annotations for the transcription")
                generate_annotations_from_transcript(
                    file_id,
                    os.path.join(upload_folder, file_name_with_id),
                    os.path.join(upload_folder, vtt_file),
                    os.path.join(upload_folder, dir_name),
                )

            print("Done extracting frames and generating annotation")
            # Delete temporary vtt file
            os.remove(os.path.join(upload_folder, vtt_file))

            # Ingest multimodal data into redis
            print("Ingesting data to redis vector store")
            ingest_multimodal(base_file_name, os.path.join(upload_folder, dir_name), embeddings)

            # Delete temporary video directory containing frames and annotations
            shutil.rmtree(os.path.join(upload_folder, dir_name))

            print(f"Processed file {file_to_ingest.filename}")
            end = time.time()
            print(str(end - st))

        return {
            "status": 200,
            "message": "Data preparation succeeded",
            "file_id_maps": uploaded_files_map,
        }

    raise HTTPException(status_code=400, detail="Must provide at least one video (.mp4) or audio (.wav) file.")


@register_microservice(
    name="opea_service@prepare_videodoc_redis", endpoint="/v1/generate_captions", host="0.0.0.0", port=6007
)
async def ingest_generate_caption(files: List[UploadFile] = File(None)):
    """Upload images and videos without speech (only background music or no audio), generate captions using lvm microservice and ingest into redis."""

    if files:
        file_paths = []
        uploaded_files_saved_files_map = {}
        for file in files:
            if os.path.splitext(file.filename)[1] in [".mp4", ".png", ".jpg", ".jpeg", ".gif"]:
                file_paths.append(file)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not a supported file type. Please upload mp4, png, jpg, jpeg, and gif files only.",
                )

        for file in file_paths:
            print(f"Processing file {file.filename}")

            # Assign unique identifier to file
            id = generate_id()

            # Create file name by appending identifier
            name, ext = os.path.splitext(file.filename)
            file_name = f"{name}_{id}{ext}"
            dir_name = os.path.splitext(file_name)[0]

            # Save file in upload_directory
            with open(os.path.join(upload_folder, file_name), "wb") as f:
                shutil.copyfileobj(file.file, f)
            uploaded_files_saved_files_map[name] = file_name

            # Store frames and caption annotations in a new directory
            extract_frames_and_generate_captions(
                id,
                os.path.join(upload_folder, file_name),
                LVM_ENDPOINT,
                os.path.join(upload_folder, dir_name),
            )

            # Ingest multimodal data into redis
            ingest_multimodal(name, os.path.join(upload_folder, dir_name), embeddings)

            # Delete temporary directory containing frames and annotations
            # shutil.rmtree(os.path.join(upload_folder, dir_name))

            print(f"Processed file {file.filename}")

        return {
            "status": 200,
            "message": "Data preparation succeeded",
            "file_id_maps": uploaded_files_saved_files_map,
        }

    raise HTTPException(status_code=400, detail="Must provide at least one file.")


@register_microservice(
    name="opea_service@prepare_videodoc_redis",
    endpoint="/v1/ingest_with_text",
    host="0.0.0.0",
    port=6007,
)
async def ingest_with_text(files: List[UploadFile] = File(None)):
    if files:
        accepted_media_formats = [".mp4", ".png", ".jpg", ".jpeg", ".gif"]
        # Create a lookup dictionary containing all media files
        matched_files = {f.filename: [f] for f in files if os.path.splitext(f.filename)[1] in accepted_media_formats}
        uploaded_files_map = {}

        # Go through files again and match caption files to media files
        for file in files:
            file_base, file_extension = os.path.splitext(file.filename)
            if file_extension == ".vtt":
                if "{}.mp4".format(file_base) in matched_files:
                    matched_files["{}.mp4".format(file_base)].append(file)
                else:
                    print(f"No video was found for caption file {file.filename}.")
            elif file_extension == ".txt":
                if "{}.png".format(file_base) in matched_files:
                    matched_files["{}.png".format(file_base)].append(file)
                elif "{}.jpg".format(file_base) in matched_files:
                    matched_files["{}.jpg".format(file_base)].append(file)
                elif "{}.jpeg".format(file_base) in matched_files:
                    matched_files["{}.jpeg".format(file_base)].append(file)
                elif "{}.gif".format(file_base) in matched_files:
                    matched_files["{}.gif".format(file_base)].append(file)
                else:
                    print(f"No image was found for caption file {file.filename}.")
            elif file_extension not in accepted_media_formats:
                print(f"Skipping file {file.filename} because of unsupported format.")

        # Check if every media file has a caption file
        for media_file_name, file_pair in matched_files.items():
            if len(file_pair) != 2:
                raise HTTPException(status_code=400, detail=f"No caption file found for {media_file_name}")

        if len(matched_files.keys()) == 0:
            return HTTPException(
                status_code=400,
                detail="The uploaded files have unsupported formats. Please upload at least one video file (.mp4) with captions (.vtt) or one image (.png, .jpg, .jpeg, or .gif) with caption (.txt)",
            )

        for media_file in matched_files:
            print(f"Processing file {media_file}")

            # Assign unique identifier to file
            file_id = generate_id()

            # Create file name by appending identifier
            file_name, file_extension = os.path.splitext(media_file)
            media_file_name = f"{file_name}_{file_id}{file_extension}"
            media_dir_name = os.path.splitext(media_file_name)[0]

            # Save file in upload_directory
            with open(os.path.join(upload_folder, media_file_name), "wb") as f:
                shutil.copyfileobj(matched_files[media_file][0].file, f)
            uploaded_files_map[file_name] = media_file_name

            # Save caption file in upload directory
            caption_file_extension = os.path.splitext(matched_files[media_file][1].filename)[1]
            caption_file = f"{media_dir_name}{caption_file_extension}"
            with open(os.path.join(upload_folder, caption_file), "wb") as f:
                shutil.copyfileobj(matched_files[media_file][1].file, f)

            # Store frames and caption annotations in a new directory
            extract_frames_and_annotations_from_transcripts(
                file_id,
                os.path.join(upload_folder, media_file_name),
                os.path.join(upload_folder, caption_file),
                os.path.join(upload_folder, media_dir_name),
            )

            # Delete temporary caption file
            os.remove(os.path.join(upload_folder, caption_file))

            # Ingest multimodal data into redis
            ingest_multimodal(file_name, os.path.join(upload_folder, media_dir_name), embeddings)

            # Delete temporary media directory containing frames and annotations
            shutil.rmtree(os.path.join(upload_folder, media_dir_name))

            print(f"Processed file {media_file}")

        return {
            "status": 200,
            "message": "Data preparation succeeded",
            "file_id_maps": uploaded_files_map,
        }

    raise HTTPException(
        status_code=400,
        detail="Must provide at least one pair consisting of video (.mp4) and captions (.vtt) or image (.png, .jpg, .jpeg, .gif) with caption (.txt)",
    )


@register_microservice(
    name="opea_service@prepare_videodoc_redis", endpoint="/v1/dataprep/get_files", host="0.0.0.0", port=6007
)
async def rag_get_file_structure():
    """Returns list of names of uploaded videos saved on the server."""

    if not Path(upload_folder).exists():
        print("No file uploaded, return empty list.")
        return []

    uploaded_videos = os.listdir(upload_folder)
    return uploaded_videos


@register_microservice(
    name="opea_service@prepare_videodoc_redis", endpoint="/v1/dataprep/delete_files", host="0.0.0.0", port=6007
)
async def delete_files():
    """Delete all uploaded files along with redis index."""
    index_deleted = drop_index(index_name=INDEX_NAME)

    if not index_deleted:
        raise HTTPException(status_code=409, detail="Uploaded files could not be deleted. Index does not exist")

    clear_upload_folder(upload_folder)
    print("Successfully deleted all uploaded files.")
    return {"status": True}


if __name__ == "__main__":
    create_upload_folder(upload_folder)
    # Load embeddings model
    print("Initializing BridgeTower model as embedder...")
    embeddings = BridgeTowerEmbedding(model_name=EMBED_MODEL, device=device)
    print("Done initialization of embedder!")
    opea_microservices["opea_service@prepare_videodoc_redis"].start()
