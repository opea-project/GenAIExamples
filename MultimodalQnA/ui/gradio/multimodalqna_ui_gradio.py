# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import glob
import os
import shutil
import time
from pathlib import Path

import gradio as gr
import requests
import uvicorn
from conversation import multimodalqna_conv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from gradio_pdf import PDF
from utils import (
    AUDIO_FORMATS,
    IMAGE_FORMATS,
    TMP_DIR,
    build_logger,
    convert_base64_to_audio,
    make_temp_image,
    server_error_msg,
    split_audio,
    split_video,
)

logger = build_logger("gradio_web_server", "gradio_web_server.log")
logflag = os.getenv("LOGFLAG", False)

ui_timeout = int(os.getenv("UI_TIMEOUT", 200))

headers = {"Content-Type": "application/json"}

css = """
h1 {
    text-align: center;
    display:block;
}
"""
tmp_upload_folder = "/tmp/gradio/"

# create a FastAPI app
app = FastAPI()
cur_dir = os.getcwd()
static_dir = Path(os.path.join(cur_dir, "static/"))
tmp_dir = Path(os.path.join(cur_dir, "split_tmp_videos/"))
audio_tmp_dir = Path(os.path.join(cur_dir, "split_tmp_audios/"))

Path(static_dir).mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

description = "This Space lets you engage with MultimodalQnA on a video through a chat box."

no_change_btn = gr.Button()
enable_btn = gr.Button(interactive=True)
disable_btn = gr.Button(interactive=False)


def clear_history(state, request: gr.Request):
    logger.info(f"clear_history. ip: {request.client.host}")
    if state.split_audio and os.path.exists(state.split_audio):
        os.remove(state.split_audio)
    if state.split_video and os.path.exists(state.split_video):
        os.remove(state.split_video)
    if state.image and os.path.exists(state.image):
        os.remove(state.image)
    if state.pdf and os.path.exists(state.pdf):
        os.remove(state.pdf)
    state = multimodalqna_conv.copy()
    state.chatbot_history = []
    for file in glob.glob(os.path.join(TMP_DIR, "*.wav")):
        os.remove(file)  # This removes all chatbot assistant's voice response files
    audio = gr.Audio(value=None, elem_id="audio", visible=False, label="Media")
    video = gr.Video(value=None, elem_id="video", visible=True, label="Media")
    image = gr.Image(value=None, elem_id="image", visible=False, label="Media")
    pdf = PDF(value=None, elem_id="pdf", interactive=False, visible=False, label="Media")
    return (state, state.to_gradio_chatbot(), None, audio, video, image, pdf) + (disable_btn,) * 1


def add_text(state, multimodal_textbox, request: gr.Request):
    text = multimodal_textbox["text"]
    files = multimodal_textbox["files"]

    image_file, audio_file = None, None

    text = text.strip()

    if not text and not files:
        state.skip_next = True
        return (state, state.to_gradio_chatbot(), None) + (no_change_btn,) * 1

    text = text[:2000]  # Hard cut-off

    state.skip_next = False

    if files:
        if Path(files[0]).suffix in IMAGE_FORMATS:
            image_file = files[0]
        if Path(files[0]).suffix in AUDIO_FORMATS or len(files) > 1:
            audio_file = files[-1]  # Guaranteed that last file would be recorded audio

    # Add to chatbot history
    if image_file:
        state.image_query_file = image_file
        state.chatbot_history.append({"role": state.roles[0], "content": {"path": image_file}})
    if audio_file:
        state.audio_query_file = audio_file
        state.chatbot_history.append({"role": state.roles[0], "content": {"path": audio_file}})

    state.chatbot_history.append({"role": state.roles[0], "content": text})

    logger.info(f"add_text. ip: {request.client.host}. len: {len(text)}")

    return (state, state.to_gradio_chatbot(), gr.MultimodalTextbox(value=None)) + (disable_btn,) * 1


def http_bot(state, audio_response_toggler, request: gr.Request):
    global gateway_addr
    logger.info(f"http_bot. ip: {request.client.host}")
    url = gateway_addr

    if state.skip_next:
        # This generate call is skipped due to invalid inputs
        yield (state, state.to_gradio_chatbot(), None, None, None, None) + (no_change_btn,) * 1
        return

    is_very_first_query = all(True if h["role"] == "user" else False for h in state.chatbot_history)

    # Construct prompt
    prompt = state.get_prompt(is_very_first_query)

    modalities = ["text", "audio"] if audio_response_toggler else ["text"]

    # Make requests
    pload = {"messages": prompt, "modalities": modalities}

    state.chatbot_history.append({"role": state.roles[1], "content": "▌"})

    yield (state, state.to_gradio_chatbot(), state.split_audio, state.split_video, state.image, state.pdf) + (
        disable_btn,
    ) * 1

    if logflag:
        logger.info(f"==== request ====\n{pload}")
    logger.info(f"==== url request ====\n{gateway_addr}")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=pload,
            timeout=ui_timeout,
        )
        logger.info(response.status_code)
        if logflag:
            logger.info(response.json())

        if response.status_code == 200:
            response = response.json()
            choice = response["choices"][-1]
            metadata = choice["metadata"]
            message = choice["message"]["content"]
            audio_response = None
            if audio_response_toggler:
                if choice["message"]["audio"]:
                    audio_response = choice["message"]["audio"]["data"]

            if (
                is_very_first_query
                and not state.video_file
                and metadata
                and "source_video" in metadata
                and not state.time_of_frame_ms
                and "time_of_frame_ms" in metadata
            ):
                video_file = metadata["source_video"]
                state.video_file = os.path.join(static_dir, metadata["source_video"])
                state.time_of_frame_ms = metadata["time_of_frame_ms"]
                state.caption = metadata["transcript_for_inference"]
                file_ext = os.path.splitext(state.video_file)[-1]
                if file_ext == ".mp4":
                    try:
                        splited_video_path = split_video(
                            state.video_file, state.time_of_frame_ms, tmp_dir, f"{state.time_of_frame_ms}__{video_file}"
                        )
                    except:
                        print(f"video {state.video_file} does not exist in UI host!")
                        splited_video_path = None
                    state.split_video = splited_video_path
                elif file_ext in AUDIO_FORMATS:
                    try:
                        splited_audio_path = split_audio(
                            state.video_file,
                            state.time_of_frame_ms,
                            audio_tmp_dir,
                            f"{state.time_of_frame_ms}__{video_file}",
                        )
                    except:
                        print(f"audio {state.video_file} does not exist in UI host!")
                        splited_audio_path = None
                    state.split_audio = splited_audio_path
                elif file_ext in IMAGE_FORMATS:
                    try:
                        output_image_path = make_temp_image(state.video_file, file_ext)
                    except:
                        print(f"image {state.video_file} does not exist in UI host!")
                        output_image_path = None
                    state.image = output_image_path
                elif file_ext == ".pdf":
                    try:
                        output_pdf_path = make_temp_image(state.video_file, file_ext)
                    except:
                        print(f"pdf {state.video_file} does not exist in UI host!")
                        output_pdf_path = None
                    state.pdf = output_pdf_path
        else:
            raise requests.exceptions.RequestException

    except requests.exceptions.RequestException as e:
        if logflag:
            logger.info(f"Request Exception occurred:\n{str(e)}")

        gr.Error("Request exception occurred. See logs for details.")

        yield (state, state.to_gradio_chatbot(), None, None, None, None) + (enable_btn,)
        return

    if audio_response:
        state.chatbot_history[-1]["content"] = {"path": convert_base64_to_audio(audio_response)}
    else:
        state.chatbot_history[-1]["content"] = message

    yield (
        state,
        state.to_gradio_chatbot(),
        gr.Audio(state.split_audio, visible=state.split_audio is not None),
        gr.Video(state.split_video, visible=state.split_video is not None),
        gr.Image(state.image, visible=state.image is not None),
        PDF(
            state.pdf,
            visible=state.pdf is not None,
            interactive=False,
            starting_page=int(state.time_of_frame_ms) if state.time_of_frame_ms else 0,
        ),
    ) + (enable_btn,) * 1

    logger.info(f"{state.chatbot_history[-1]['content']}")
    return


def ingest_gen_transcript(filepath, filetype, request: gr.Request):
    yield (
        gr.Textbox(visible=True, value=f"Please wait while your uploaded {filetype} is ingested into the database...")
    )
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print(f"Found malicious {filetype} file name!")
        yield (
            gr.Textbox(
                visible=True,
                value=f"Your uploaded {filetype}'s file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    print("Done copying uploaded file to static folder.")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = {
        "files": open(dest, "rb"),
    }
    response = requests.post(dataprep_gen_transcript_addr, headers=headers, files=files)
    logger.info(response.status_code)
    if response.status_code == 200:
        response = response.json()
        if logflag:
            logger.info(response)
        yield (gr.Textbox(visible=True, value=f"The {filetype} ingestion is done. Saving your uploaded {filetype}..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value=f"Congratulations, your upload is done!\nClick the X button on the top right of the {filetype} upload box to upload another {filetype}.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the {filetype} upload box to reupload your video.",
            )
        )
        time.sleep(2)
    return


def ingest_gen_caption(filepath, filetype, request: gr.Request):
    yield (
        gr.Textbox(visible=True, value=f"Please wait while your uploaded {filetype} is ingested into the database...")
    )
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print(f"Found malicious {filetype} file name!")
        yield (
            gr.Textbox(
                visible=True,
                value=f"Your uploaded {filetype}'s file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    print("Done copying uploaded file to static folder.")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = {
        "files": open(dest, "rb"),
    }
    response = requests.post(dataprep_gen_caption_addr, headers=headers, files=files)
    logger.info(response.status_code)
    if response.status_code == 200:
        response = response.json()
        if logflag:
            logger.info(response)
        yield (gr.Textbox(visible=True, value=f"The {filetype} ingestion is done. Saving your uploaded {filetype}..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value=f"Congratulations, your upload is done!\nClick the X button on the top right of the {filetype} upload box to upload another {filetype}.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the {filetype} upload box to reupload your video.",
            )
        )
        time.sleep(2)
    return


def ingest_with_caption(filepath, text_caption, audio_caption, request: gr.Request):
    yield (gr.Textbox(visible=True, value="Please wait for your uploaded image to be ingested into the database..."))

    # Process the image
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print("Found malicious image file name!")
        yield (
            gr.Textbox(
                visible=True,
                value="Your uploaded image's file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)

    # Process the caption (can be text or audio)
    is_audio_caption = audio_caption is not None
    if is_audio_caption:
        verified_audio_path = os.path.normpath(audio_caption)
        if not verified_audio_path.startswith(static_dir):
            print("Found malicious audio file path!")
            yield (
                gr.Textbox(
                    visible=True,
                    value="Your uploaded audio file's path is not allowed. Please upload a valid file.",
                )
            )
            return
        caption_basename = "{}{}".format(os.path.splitext(basename)[0], os.path.splitext(verified_audio_path)[-1])
        caption_file = verified_audio_path
    else:
        caption_basename = "{}.txt".format(os.path.splitext(basename)[0])
        caption_file = os.path.join(static_dir, caption_basename)
        with open(caption_file, "w") as file:
            file.write(text_caption)

    print("Done copying uploaded files to static folder!")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = [("files", (basename, open(dest, "rb"))), ("files", (caption_basename, open(caption_file, "rb")))]
    try:
        response = requests.post(dataprep_ingest_addr, headers=headers, files=files)
    finally:
        if not is_audio_caption:
            os.remove(caption_file)
    logger.info(response.status_code)
    if response.status_code == 200:
        response = response.json()
        if logflag:
            logger.info(response)
        yield (gr.Textbox(visible=True, value="Image ingestion is done. Saving your uploaded image..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value="Congratulation! Your upload is done!\nClick the X button on the top right of the image upload box to upload another image.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the image upload box to reupload your image!",
            )
        )
        time.sleep(2)
    return


def ingest_pdf(filepath, request: gr.Request):
    yield (gr.Textbox(visible=True, value="Please wait while your uploaded PDF is ingested into the database..."))
    verified_filepath = os.path.normpath(filepath)
    if not verified_filepath.startswith(tmp_upload_folder):
        print("Found malicious PDF file name!")
        yield (
            gr.Textbox(
                visible=True,
                value="Your uploaded PDF's file name has special characters that are not allowed (depends on the OS, some examples are \, /, :, and *). Please consider changing the file name.",
            )
        )
        return
    basename = os.path.basename(verified_filepath)
    dest = os.path.join(static_dir, basename)
    shutil.copy(verified_filepath, dest)
    print("Done copying uploaded file to static folder.")
    headers = {
        # 'Content-Type': 'multipart/form-data'
    }
    files = {
        "files": open(dest, "rb"),
    }
    response = requests.post(dataprep_ingest_addr, headers=headers, files=files)
    print(response.status_code)
    if response.status_code == 200:
        response = response.json()
        yield (gr.Textbox(visible=True, value="The PDF ingestion is done. Saving your uploaded PDF..."))
        time.sleep(2)
        fn_no_ext = Path(dest).stem
        if "file_id_maps" in response and fn_no_ext in response["file_id_maps"]:
            new_dst = os.path.join(static_dir, response["file_id_maps"][fn_no_ext])
            print(response["file_id_maps"][fn_no_ext])
            os.rename(dest, new_dst)
            yield (
                gr.Textbox(
                    visible=True,
                    value="Congratulations, your upload is done!\nClick the X button on the top right of the PDF upload box to upload another file.",
                )
            )
            return
    else:
        yield (
            gr.Textbox(
                visible=True,
                value=f"Something went wrong (server error: {response.status_code})!\nPlease click the X button on the top right of the PDF upload box to reupload your file.",
            )
        )
        time.sleep(2)
    return


def hide_text(request: gr.Request):
    return gr.Textbox(visible=False)


def hide_text_pdf(pdf, text, request: gr.Request):
    if pdf is not None:
        return text
    else:
        return gr.Textbox(visible=False)


def clear_captions(request: gr.Request):
    return None, None


def get_files():
    try:
        response = requests.post(dataprep_get_file_addr, headers=headers)
        logger.info(response.status_code)
        files = response.json()
        if files:
            html_content = "<ul>" + "".join(f"<li>{item}</li>" for item in files) + "</ul>"
            yield (gr.HTML(html_content, visible=True, max_height=200))
            return
        else:
            yield (gr.HTML("Vector store is empty.", visible=True))
            return
    except Exception as e:
        logger.info(f"Error getting files from vector store: {str(e)}")


def delete_files():
    import json

    data = {"file_path": "all"}
    try:
        response = requests.post(dataprep_delete_file_addr, headers=headers, data=json.dumps(data))
        logger.info(response.status_code)
        yield (gr.update(value="Deleted all files!"))
        return
    except Exception as e:
        logger.info(f"Error deleting files from vector store: {str(e)}")


with gr.Blocks() as upload_video:
    gr.Markdown("# Ingest Videos Using Generated Transcripts or Captions")
    gr.Markdown("Use this interface to ingest a video and generate transcripts or captions for it")

    def select_upload_type(choice, request: gr.Request):
        if choice == "transcript":
            return gr.Video(sources="upload", visible=True, format="mp4"), gr.Video(
                sources="upload", visible=False, format="mp4"
            )
        else:
            return gr.Video(sources="upload", visible=False, format="mp4"), gr.Video(
                sources="upload", visible=True, format="mp4"
            )

    with gr.Row():
        with gr.Column(scale=6):
            video_upload_trans = gr.Video(sources="upload", elem_id="video_upload_trans", visible=True, format="mp4")
            video_upload_cap = gr.Video(sources="upload", elem_id="video_upload_cap", visible=False, format="mp4")
        with gr.Column(scale=3):
            text_options_radio = gr.Radio(
                [
                    ("Generate transcript (video contains voice)", "transcript"),
                    ("Generate captions (video does not contain voice)", "caption"),
                ],
                label="Text Options",
                info="How should text be ingested?",
                value="transcript",
            )
            text_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        video_upload_trans.upload(
            ingest_gen_transcript, [video_upload_trans, gr.Textbox(value="video", visible=False)], [text_upload_result]
        )
        video_upload_trans.clear(hide_text, [], [text_upload_result])
        video_upload_cap.upload(
            ingest_gen_caption, [video_upload_cap, gr.Textbox(value="video", visible=False)], [text_upload_result]
        )
        video_upload_cap.clear(hide_text, [], [text_upload_result])
        text_options_radio.change(select_upload_type, [text_options_radio], [video_upload_trans, video_upload_cap])

with gr.Blocks() as upload_image:
    gr.Markdown("# Ingest Images Using Generated or Custom Captions")
    gr.Markdown(
        "Use this interface to ingest an image and generate a caption for it. If uploading a caption, populate it before the image."
    )

    text_caption_label = "Text Caption"
    audio_caption_label = "Voice Audio Caption ({}, or microphone)".format(", ".join(AUDIO_FORMATS))

    def select_upload_type(choice, request: gr.Request):
        if choice == "gen_caption":
            return (
                gr.Image(sources="upload", visible=True),
                gr.Image(sources="upload", visible=False),
                gr.Textbox(visible=False, interactive=True, label=text_caption_label),
                gr.Audio(visible=False, type="filepath", label=audio_caption_label),
            )
        elif choice == "custom_caption":
            return (
                gr.Image(sources="upload", visible=False),
                gr.Image(sources="upload", visible=True),
                gr.Textbox(visible=True, interactive=True, label=text_caption_label),
                gr.Audio(visible=False, type="filepath", label=audio_caption_label),
            )
        else:
            return (
                gr.Image(sources="upload", visible=False),
                gr.Image(sources="upload", visible=True),
                gr.Textbox(visible=False, interactive=True, label=text_caption_label),
                gr.Audio(visible=True, type="filepath", label=audio_caption_label),
            )

    def verify_audio_caption_type(file, request: gr.Request):
        audio_type = os.path.splitext(file)[-1]
        if audio_type not in AUDIO_FORMATS:
            return (
                None,
                gr.Textbox(visible=True, value="The audio file format must be {}".format(" or ".join(AUDIO_FORMATS))),
            )
        else:
            return (
                gr.Audio(value=file, visible=True, type="filepath", label=audio_caption_label),
                gr.Textbox(visible=False, value=None),
            )

    with gr.Row():
        with gr.Column(scale=6):
            image_upload_cap = gr.Image(type="filepath", sources="upload", elem_id="image_upload_cap", visible=True)
            image_upload_text = gr.Image(type="filepath", sources="upload", elem_id="image_upload_cap", visible=False)
        with gr.Column(scale=3):
            text_options_radio = gr.Radio(
                [
                    ("Auto-generate a caption", "gen_caption"),
                    ("Upload a text caption (populate before image)", "custom_caption"),
                    ("Upload an audio caption (populate before image)", "custom_audio_caption"),
                ],
                label="Caption Options",
                info="How should captions be ingested?",
                value="gen_caption",
            )
            custom_caption = gr.Textbox(visible=False, interactive=True, label=text_caption_label)
            custom_caption_audio = gr.Audio(visible=False, type="filepath", label=audio_caption_label)
            text_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        custom_caption_audio.input(
            verify_audio_caption_type, [custom_caption_audio], [custom_caption_audio, text_upload_result]
        )
        image_upload_cap.upload(
            ingest_gen_caption, [image_upload_cap, gr.Textbox(value="image", visible=False)], [text_upload_result]
        )
        image_upload_cap.clear(hide_text, [], [text_upload_result])
        image_upload_text.upload(
            ingest_with_caption, [image_upload_text, custom_caption, custom_caption_audio], [text_upload_result]
        ).then(clear_captions, [], [custom_caption, custom_caption_audio])
        image_upload_text.clear(hide_text, [], [text_upload_result])
        text_options_radio.change(
            select_upload_type,
            [text_options_radio],
            [image_upload_cap, image_upload_text, custom_caption, custom_caption_audio],
        )

with gr.Blocks() as upload_audio:
    gr.Markdown("# Ingest Audio Using Generated Transcripts")
    gr.Markdown("Use this interface to ingest an audio file and generate a transcript for it")
    with gr.Row():
        with gr.Column(scale=6):
            audio_upload = gr.Audio(type="filepath")
        with gr.Column(scale=3):
            text_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        audio_upload.upload(
            ingest_gen_transcript, [audio_upload, gr.Textbox(value="audio", visible=False)], [text_upload_result]
        )
        audio_upload.stop_recording(
            ingest_gen_transcript, [audio_upload, gr.Textbox(value="audio", visible=False)], [text_upload_result]
        )
        audio_upload.clear(hide_text, [], [text_upload_result])

with gr.Blocks() as upload_pdf:
    gr.Markdown("# Ingest PDF Files")
    gr.Markdown("Use this interface to ingest a PDF file with text and images")
    with gr.Row():
        with gr.Column(scale=6):
            pdf_upload = PDF(label="PDF File")
        with gr.Column(scale=3):
            pdf_upload_result = gr.Textbox(visible=False, interactive=False, label="Upload Status")
        pdf_upload.change(hide_text_pdf, [pdf_upload, pdf_upload_result], [pdf_upload_result])
        pdf_upload.upload(ingest_pdf, [pdf_upload], [pdf_upload_result])

with gr.Blocks() as qna:
    state = gr.State(multimodalqna_conv.copy())
    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            audio = gr.Audio(elem_id="audio", visible=False, label="Media")
            video = gr.Video(elem_id="video", visible=True, label="Media")
            image = gr.Image(elem_id="image", visible=False, label="Media")
            pdf = PDF(elem_id="pdf", interactive=False, visible=False, label="Media")
        with gr.Column(scale=9):
            chatbot = gr.Chatbot(elem_id="chatbot", label="MultimodalQnA Chatbot", type="messages")
            with gr.Row(equal_height=True):
                with gr.Column(scale=8):
                    multimodal_textbox = gr.MultimodalTextbox(
                        show_label=False,
                        file_types=IMAGE_FORMATS + AUDIO_FORMATS,
                        sources=["microphone", "upload"],
                        placeholder="Text, Image & Audio Query",
                    )
                with gr.Column(scale=1, min_width=150):
                    with gr.Row():
                        audio_response_toggler = gr.Checkbox(label="Audio Responses", container=False)
                    with gr.Row(elem_id="buttons") as button_row:
                        clear_btn = gr.Button(value="🗑️  Clear", interactive=False)

    clear_btn.click(
        clear_history,
        [
            state,
        ],
        [state, chatbot, multimodal_textbox, audio, video, image, pdf, clear_btn],
    )

    multimodal_textbox.submit(
        add_text, [state, multimodal_textbox], [state, chatbot, multimodal_textbox, clear_btn]
    ).then(http_bot, [state, audio_response_toggler], [state, chatbot, audio, video, image, pdf, clear_btn]).then(
        lambda: gr.MultimodalTextbox(interactive=True), None, [multimodal_textbox]
    )

with gr.Blocks() as vector_store:
    gr.Markdown("# Uploaded Files")

    with gr.Row():
        with gr.Column(scale=6):
            files = gr.HTML(visible=False)
        with gr.Column(scale=3):
            refresh_btn = gr.Button(value="↻ Refresh", interactive=True, variant="primary")
            delete_btn = gr.Button(value="🗑️ Delete", interactive=True, variant="stop")
        refresh_btn.click(get_files, None, [files])
        delete_btn.click(delete_files, None, [files])

with gr.Blocks(css=css) as demo:
    gr.Markdown("# MultimodalQnA")
    with gr.Tabs():
        with gr.TabItem("MultimodalQnA"):
            qna.render()
        with gr.TabItem("Upload Video"):
            upload_video.render()
        with gr.TabItem("Upload Image"):
            upload_image.render()
        with gr.TabItem("Upload Audio"):
            upload_audio.render()
        with gr.TabItem("Upload PDF"):
            upload_pdf.render()
        with gr.TabItem("Vector Store"):
            vector_store.render()

demo.queue()
app = gr.mount_gradio_app(app, demo, path="/")
share = False
enable_queue = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=os.getenv("UI_PORT", 5173))
    parser.add_argument("--concurrency-count", type=int, default=20)
    parser.add_argument("--share", action="store_true")

    MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 8888)
    DATAPREP_MMR_PORT = os.getenv("DATAPREP_MMR_PORT", 6007)

    backend_service_endpoint = os.getenv(
        "BACKEND_SERVICE_ENDPOINT", f"http://localhost:{MEGA_SERVICE_PORT}/v1/multimodalqna"
    )
    dataprep_ingest_endpoint = os.getenv(
        "DATAPREP_INGEST_SERVICE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/ingest"
    )
    dataprep_gen_transcript_endpoint = os.getenv(
        "DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/generate_transcripts"
    )
    dataprep_gen_caption_endpoint = os.getenv(
        "DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/generate_captions"
    )
    dataprep_get_file_endpoint = os.getenv(
        "DATAPREP_GET_FILE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/dataprep/get"
    )
    dataprep_delete_file_endpoint = os.getenv(
        "DATAPREP_DELETE_FILE_ENDPOINT", f"http://localhost:{DATAPREP_MMR_PORT}/v1/dataprep/delete"
    )
    args = parser.parse_args()
    logger.info(f"args: {args}")
    global gateway_addr
    gateway_addr = backend_service_endpoint
    global dataprep_ingest_addr
    dataprep_ingest_addr = dataprep_ingest_endpoint
    global dataprep_gen_transcript_addr
    dataprep_gen_transcript_addr = dataprep_gen_transcript_endpoint
    global dataprep_gen_caption_addr
    dataprep_gen_caption_addr = dataprep_gen_caption_endpoint
    global dataprep_get_file_addr
    dataprep_get_file_addr = dataprep_get_file_endpoint
    global dataprep_delete_file_addr
    dataprep_delete_file_addr = dataprep_delete_file_endpoint

    uvicorn.run(app, host=args.host, port=args.port)
