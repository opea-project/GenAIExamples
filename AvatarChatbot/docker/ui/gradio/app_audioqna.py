# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import io
import os
import subprocess
import time

import aiohttp
import gradio as gr
import numpy as np
import requests
import soundfile as sf
from PIL import Image


# %% AudioQnA functions
def preprocess_audio(audio):
    """The audio data is a 16-bit integer array with values ranging from -32768 to 32767 and the shape of the audio data array is (samples,)"""
    sr, y = audio
    # Convert to normalized float32 audio
    y = y.astype(np.float32)
    y /= np.max(np.abs(y))
    # Convert the normalized float32 audio to a WAV file in memory
    buf = io.BytesIO()
    sf.write(buf, y, sr, format="WAV")
    buf.seek(0)  # Reset the buffer position to the beginning
    # Encode the WAV file to base64 string
    base64_bytes = base64.b64encode(buf.read())
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


def base64_to_int16(base64_string):
    wav_bytes = base64.b64decode(base64_string)
    buf = io.BytesIO(wav_bytes)
    y, sr = sf.read(buf, dtype="int16")
    return sr, y


async def transcribe(audio):
    """Input: mic audio; Output: ai audio, text, text"""
    global ai_chatbot_url, chat_history
    base64bytestr = preprocess_audio(audio)
    # Send the audio to the backend server
    initial_inputs = {"audio": base64bytestr, "max_tokens": 64}

    async with aiohttp.ClientSession() as session:
        async with session.post(ai_chatbot_url, json=initial_inputs) as response:
            # response = requests.post(ai_chatbot_url, json=initial_inputs)
            # Check the response status code
            if response.status == 200:
                response_text = await response.json()
                # with open("response.txt", "w") as file:
                #     file.write(response)
                # Decode the base64 string
                sampling_rate, audio_int16 = base64_to_int16(response_text)
                return (sampling_rate, audio_int16)  # handle the response
            else:
                return {"error": "Failed to transcribe audio", "status_code": response.status_code}


# %% Wav2Lip functions
async def gen_video(image, audio):
    """Input: image (saved .png path), ai audio (saved .wav path); Output: video"""
    # 0. Preprocess audio
    # buf = io.BytesIO()
    sr, y = audio
    output_audio_save_path = "inputs/intermediate.wav"
    sf.write(output_audio_save_path, y, sr, format="WAV")

    # 1. Set environment variables
    os.environ["INFERENCE_MODE"] = "wav2clip_only"
    os.environ["CHECKPOINT_PATH"] = "src/Wav2Lip/checkpoints/wav2lip_gan.pth"
    os.environ["FACE"] = image  # path to either an image or a video
    os.environ["AUDIO"] = output_audio_save_path  # path to .wav audio
    # os.environ['AUDIO'] = audio
    os.environ["FACESIZE"] = "96"
    os.environ["OUTFILE"] = "outputs/result6.mp4"
    os.environ["GFPGAN_MODEL_VERSION"] = "1.3"
    os.environ["UPSCALE_FACTOR"] = "1"  # int
    # os.environ['FPS'] = '25.' # can be lower (e.g., 10)
    os.environ["FPS"] = "10."  # can be lower when using an image (e.g., 10)

    # 2. Run inference.sh bash script to perform Wav2Lip+GFPGAN inference
    # Output video is saved at the path 'OUTFILE'
    command_wav2lip_gfpgan = "bash inference_vars.sh"
    subprocess.run(command_wav2lip_gfpgan, shell=True)

    outfile = os.environ.get("OUTFILE")
    if os.path.exists(outfile):
        res_video = outfile
    else:
        res_video = "inputs/loading.mp4"
    return res_video


# %% AI Avatar demo function
# ctao 7/19 - make it asynchronous
async def aiavatar_demo(audio):
    """Input: mic audio, image; Output: ai audio, text, text, ai video"""
    # Include AudioQnA
    output_audio = await transcribe(audio)  # AudioQnA

    if isinstance(output_audio, dict):  # in case of an error
        return None, None
    else:
        sr, audio_int16 = output_audio
        audio_file = "outputs/output_audio.wav"
        sf.write(audio_file, audio_int16, sr)
        # return audio_file, audio_file, image
        return audio_file


async def final_update(audio, image):
    res_video = await gen_video(image, audio)
    return res_video


# %% Main
if __name__ == "__main__":
    HOST_IP = os.getenv("host_ip")

    # Fetch the AudioQnA backend server
    ai_chatbot_url = f"http://{HOST_IP}:3008/v1/audioqna"

    # Collect chat history to print in the interface
    chat_history = ""

    # Prepare 3 image paths
    # HOME = os.getenv("HOME")
    # HOME="/mnt/localdisk4"
    HOME = "/home/demo/"
    image_paths = [
        Image.open(os.path.join("./assets/avatar1.jpg")),
        Image.open(os.path.join("./assets/avatar5.png")),
        Image.open(os.path.join("./assets/pallavi.png")),
    ]

    def image_to_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Convert your images to Base64
    opea_qr_base64 = image_to_base64("./assets/opea_qr.png")
    opea_gh_qr_base64 = image_to_base64("./assets/opea_gh_qr.png")
    xeon_base64 = image_to_base64("./assets/xeon.jpg")
    gaudi_base64 = image_to_base64("./assets/gaudi.png")

    # Directories
    if not os.path.exists("inputs"):
        os.makedirs("inputs")
    if not os.path.exists("temp"):
        os.makedirs("temp")
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    # Demo frontend
    demo = gr.Blocks()
    with demo:
        # Define processing functions
        count = 0

        def initial_process(audio):
            global count
            start_time = time.time()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_file = loop.run_until_complete(aiavatar_demo(audio))
            count += 1
            end_time = time.time()
            return audio_file, gr.State(value=str(count)), f"{(end_time - start_time):.1f} seconds"

        def final_process(audio, image):
            start_time = time.time()
            # loop = asyncio.get_event_loop()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res_video = loop.run_until_complete(final_update(audio, image))
            end_time = time.time()
            return res_video, f"{(end_time - start_time):.1f} seconds"

        def update_selected_image_state(image_index):
            selected_image_state.value = image_index
            # change image_input here
            return f"inputs/face_{image_index}.png"

        # UI Components
        # Title & Introduction
        gr.Markdown(
            "<h1 style='font-size: 36px;'>Using OPEA to implement a RAG-Powered Human-Like AI Avatar Audio Chatbot</h1>"
        )
        # gr.Markdown("# **Using OPEA to implement a RAG-Powered Human-Like AI Avatar Audio Chatbot**")
        with gr.Row():
            with gr.Column(scale=8):
                gr.Markdown(
                    """
                <p style='font-size: 20px;'>Welcome to our AI Avatar Audio Chatbot! This application leverages OPEA (Open Platform for Enterprise AI) to provide you with a human-like conversational experience. It employs the AudioQnA megaservice to generate an expert answer based on your query, and then animates the avatar figure with output audio. Feel free to interact with the AI avatar by choosing your own avatar and talking into the mic. </p>
                            """
                )
                gr.Image("./assets/flowchart.png", label="Megaservice Flowchart")

            with gr.Column(scale=1):
                with gr.Row():
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{opea_qr_base64}' alt='OPEA QR Code' style='width: 150px; height: auto;'>
                    """,
                        label="OPEA QR Code",
                    )
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{opea_gh_qr_base64}' alt='OPEA GitHub QR Code' style='width: 150px; height: auto;'>
                    """,
                        label="OPEA GitHub QR Code",
                    )
                with gr.Row():
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{gaudi_base64}' alt='Intel®Gaudi' style='width: 100px; height: auto;'>""",
                        label="Intel®Gaudi",
                    )
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{xeon_base64}' alt='Intel®Xeon' style='width: 100px; height: auto;'>""",
                        label="Intel®Xeon",
                    )

        # Inputs
        # Image gallery
        selected_image_state = gr.State(value=-1)
        image_clicks = []
        image_click_buttons = []
        gr.Markdown("<hr>")  # Divider
        with gr.Row():
            with gr.Column(scale=1):
                audio_input = gr.Audio(sources=None, format="wav", label="🎤 or 📤 for your Input audio!")
                image_input = gr.File(
                    file_count="single",
                    file_types=["image", "video"],
                    label="Choose an avatar or 📤 an image or video!",
                )
            with gr.Column(scale=2):
                with gr.Row():
                    for i, image_path in enumerate(image_paths):
                        save_path = f"inputs/face_{i}.png"
                        image_path.save(save_path, "PNG")
                        image_clicks.append(gr.Image(type="filepath", value=save_path, label=f"Avatar {i+1}"))
                with gr.Row():
                    for i in range(len(image_paths)):
                        image_click_buttons.append(gr.Button(f"Use Avatar {i+1}"))
        submit_button = gr.Button("Submit")

        # Outputs
        gr.Markdown("<hr>")  # Divider
        with gr.Row():
            with gr.Column(scale=1):
                audio_output_interm = gr.Audio(label="🔊 Output audio", autoplay=True)
                audio_time_text = gr.Textbox(label="Audio processing time", value="0.0 seconds")
            with gr.Column(scale=2):
                video_output = gr.Video(label="Your AI Avatar video: ", format="mp4", width=1280, height=720)
                video_time_text = gr.Textbox(label="Video processing time", value="0.0 seconds")

        # States
        interm_state = gr.State(value="initial")

        # State transitions
        for i, image_path in enumerate(image_paths):
            image_click_buttons[i].click(
                update_selected_image_state, inputs=[gr.Number(value=i, visible=False)], outputs=[image_input]
            )
        # submit_button = gr.Button("Submit")
        submit_button.click(
            initial_process,
            inputs=[audio_input],
            outputs=[audio_output_interm, interm_state, audio_time_text],  # need to change interm_state
        )
        interm_state.change(
            final_process,
            inputs=[audio_output_interm, image_input],
            outputs=[video_output, video_time_text],
        )

        demo.queue().launch(server_name="0.0.0.0", server_port=7861)
