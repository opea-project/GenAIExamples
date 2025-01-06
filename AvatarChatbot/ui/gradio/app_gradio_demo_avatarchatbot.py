# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import io
import os
import shutil
import subprocess
import time

import aiohttp
import docker
import ffmpeg
import gradio as gr
import numpy as np
import soundfile as sf
from PIL import Image


# %% Docker Management
def update_env_var_in_container(container_name, env_var, new_value):
    return


# %% AudioQnA functions
def preprocess_audio(audio):
    """The audio data is a 16-bit integer array with values ranging from -32768 to 32767 and the shape of the audio data array is (samples,)"""
    sr, y = audio

    # Convert to normalized float32 audio
    y = y.astype(np.float32)
    y /= np.max(np.abs(y))

    # Save to memory
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


async def transcribe(audio_input, face_input, model_choice):
    """Input: mic audio; Output: ai audio, text, text"""
    global ai_chatbot_url, chat_history, count
    chat_history = ""
    # Preprocess the audio
    base64bytestr = preprocess_audio(audio_input)

    # Send the audio to the AvatarChatbot backend server endpoint
    initial_inputs = {"audio": base64bytestr, "max_tokens": 64}

    # TO-DO: update wav2lip-service with the chosen face_input
    # update_env_var_in_container("wav2lip-service", "DEVICE", "new_device_value")

    async with aiohttp.ClientSession() as session:
        async with session.post(ai_chatbot_url, json=initial_inputs) as response:

            # Check the response status code
            if response.status == 200:
                # response_json = await response.json()
                # # Decode the base64 string
                # sampling_rate, audio_int16 = base64_to_int16(response_json["byte_str"])
                # chat_history += f"User: {response_json['query']}\n\n"
                # chat_ai = response_json["text"]
                # hitted_ends = [",", ".", "?", "!", "。", ";"]
                # last_punc_idx = max([chat_ai.rfind(punc) for punc in hitted_ends])
                # if last_punc_idx != -1:
                #     chat_ai = chat_ai[: last_punc_idx + 1]
                # chat_history += f"AI: {chat_ai}"
                # chat_history = chat_history.replace("OPEX", "OPEA")
                # return (sampling_rate, audio_int16)  # handle the response

                result = await response.text()
                return "docker_compose/intel/hpu/gaudi/result.mp4"
            else:
                return {"error": "Failed to transcribe audio", "status_code": response.status_code}


def resize_image(image_pil, size=(720, 720)):
    """Resize the image to the specified size."""
    return image_pil.resize(size, Image.LANCZOS)


def resize_video(video_path, save_path, size=(720, 1280)):
    """Resize the video to the specified size, and save to the save path."""
    ffmpeg.input(video_path).output(save_path, vf=f"scale={size[0]}:{size[1]}").overwrite_output().run()


# %% AI Avatar demo function
async def aiavatar_demo(audio_input, face_input, model_choice):
    """Input: mic/preloaded audio, avatar file path;
    Output: ai video"""
    # Wait for response from AvatarChatbot backend
    output_video = await transcribe(audio_input, face_input, model_choice)  # output video path

    if isinstance(output_video, dict):  # in case of an error
        return None, None
    else:
        return output_video


# %% Main
if __name__ == "__main__":
    # HOST_IP = os.getenv("host_ip")
    HOST_IP = subprocess.check_output("hostname -I | awk '{print $1}'", shell=True).decode("utf-8").strip()

    # Fetch the AudioQnA backend server
    ai_chatbot_url = f"http://{HOST_IP}:3009/v1/avatarchatbot"

    # Collect chat history to print in the interface
    chat_history = ""

    # Prepare 3 image paths and 3 video paths
    # image_pils = [
    #     Image.open(os.path.join("assets/img/woman1.png")),
    #     Image.open(os.path.join("assets/img/man1.png")),
    #     Image.open(os.path.join("assets/img/woman2.png")),
    # ]

    # video_paths = [
    #     os.path.join("assets/video/man1.mp4"),
    #     os.path.join("assets/video/woman2.mp4"),
    #     os.path.join("assets/video/man4.mp4"),
    # ]

    def image_to_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Convert your images to Base64
    xeon_base64 = image_to_base64("assets/img/xeon.jpg")
    gaudi_base64 = image_to_base64("assets/img/gaudi.png")

    # List of prerecorded WAV files containing audio questions
    # audio_filepaths = [
    #     "assets/audio/intel2.wav",
    #     "assets/audio/intel4.wav",
    # ]
    # audio_questions = [
    #     "1. What's the objective of the Open Platform for Enterprise AI? How is it helpful to enterprises building AI solutions?",
    #     "2. What kinds of Intel AI tools are available to accelerate AI workloads?",
    # ]

    # Demo frontend
    demo = gr.Blocks()
    with demo:
        # Define processing functions
        count = 0

        # Make necessary folders:
        if not os.path.exists("inputs"):
            os.makedirs("inputs")
        if not os.path.exists("outputs"):
            os.makedirs("outputs")

        def initial_process(audio_input, face_input, model_choice):
            global count
            start_time = time.time()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            video_file = loop.run_until_complete(aiavatar_demo(audio_input, face_input, model_choice))
            count += 1
            end_time = time.time()
            return video_file, f"The entire application took {(end_time - start_time):.1f} seconds"

        # def update_selected_image_state(image_index):
        #     image_index = int(image_index)
        #     selected_image_state.value = image_index
        #     # change image_input here
        #     if image_index < len(image_pils):
        #         return f"inputs/face_{image_index}.png"
        #     else:
        #         return f"inputs/video_{image_index - len(image_pils)}.mp4"

        # def update_audio_input(audio_choice):
        #     if audio_choice:
        #         audio_index = int(audio_choice.split(".")[0]) - 1
        #         audio_filepath_gradio = f"inputs/audio_{audio_index:d}.wav"
        #         shutil.copyfile(audio_filepaths[audio_index], audio_filepath_gradio)
        #         return audio_filepath_gradio

        # UI Components
        # Title & Introduction
        gr.Markdown("<h1 style='font-size: 36px;'>A PyTorch and OPEA based AI Avatar Audio Chatbot</h1>")
        with gr.Row():
            with gr.Column(scale=8):
                gr.Markdown(
                    """
                <p style='font-size: 24px;'>Welcome to our AI Avatar Audio Chatbot! This application leverages PyTorch and <strong>OPEA (Open Platform for Enterprise AI) v0.8</strong> to provide you with a human-like conversational experience. It's run on Intel® Gaudi® AI Accelerator and Intel® Xeon® Processor, with hardware and software optimizations.<br>
                Please feel free to interact with the AI avatar by choosing your own avatar and talking into the mic.</p>
                            """
                )
            with gr.Column(scale=1):
                # with gr.Row():
                #     gr.Markdown(f"""
                #     <img src='data:image/png;base64,{opea_qr_base64}' alt='OPEA QR Code' style='width: 150px; height: auto;'>
                #     """, label="OPEA QR Code")
                #     gr.Markdown(f"""
                #     <img src='data:image/png;base64,{opea_gh_qr_base64}' alt='OPEA GitHub QR Code' style='width: 150px; height: auto;'>
                #     """, label="OPEA GitHub QR Code")
                with gr.Row():
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{gaudi_base64}' alt='Intel®Gaudi' style='width: 120px; height: auto;'>""",
                        label="Intel®Gaudi",
                    )
                    gr.Markdown(
                        f"""
                    <img src='data:image/png;base64,{xeon_base64}' alt='Intel®Xeon' style='width: 120px; height: auto;'>""",
                        label="Intel®Xeon",
                    )
        gr.Markdown("<hr>")  # Divider

        # Inputs
        # Image gallery
        selected_image_state = gr.State(value=-1)
        image_clicks = []
        image_click_buttons = []
        video_clicks = []
        video_click_buttons = []
        with gr.Row():
            with gr.Column(scale=1):
                audio_input = gr.Audio(
                    sources=["upload", "microphone"], format="wav", label="🎤 or 📤 for your Input audio!"
                )
                # audio_choice = gr.Dropdown(
                #     choices=audio_questions,
                #     label="Choose an audio question",
                #     value=None,  # default value
                # )
                # Update audio_input when a selection is made from the dropdown
                # audio_choice.change(fn=update_audio_input, inputs=audio_choice, outputs=audio_input)

                face_input = gr.File(
                    file_count="single",
                    file_types=["image", "video"],
                    label="Choose an avatar or 📤 an image or video!",
                )
                model_choice = gr.Dropdown(
                    choices=["wav2lip", "wav2lip+GAN", "wav2lip+GFPGAN"],
                    label="Choose a DL model",
                )
            # with gr.Column(scale=2):
            #     # Display 3 images and buttons
            #     with gr.Row():
            #         for i, image_pil in enumerate(image_pils):
            #             image_pil = resize_image(image_pil)
            #             save_path = f"inputs/face_{int(i)}.png"
            #             image_pil.save(save_path, "PNG")
            #             image_clicks.append(gr.Image(type="filepath", value=save_path, label=f"Avatar {int(i)+1}"))
            #     with gr.Row():
            #         for i in range(len(image_pils)):
            #             image_click_buttons.append(gr.Button(f"Use Image {i+1}"))

            #     # Display 3 videos and buttons
            #     with gr.Row():
            #         for i, video_path in enumerate(video_paths):
            #             save_path = f"inputs/video_{int(i)}.mp4"
            #             resize_video(video_path, save_path)
            #             video_clicks.append(gr.Video(value=save_path, label=f"Video {int(i)+1}"))
            #     with gr.Row():
            #         for i in range(len(video_paths)):
            #             video_click_buttons.append(gr.Button(f"Use Video {int(i)+1}"))

        submit_button = gr.Button("Submit")

        # Outputs
        gr.Markdown("<hr>")  # Divider
        with gr.Row():
            with gr.Column():
                video_output = gr.Video(label="Your AI Avatar video: ", format="mp4", width=1280, height=720)
                video_time_text = gr.Textbox(label="Video processing time", value="0.0 seconds")

        # Technical details
        gr.Markdown("<hr>")  # Divider
        with gr.Row():
            gr.Markdown(
                """
                <p style='font-size: 24px;'>OPEA megaservice deployed: <br>
                <ul style='font-size: 24px;'>
                    <li><strong>AvatarChatbot</strong></li>
                </ul></p>
                <p style='font-size: 24px;'>OPEA microservices deployed:
                <ul style='font-size: 24px;'>
                    <li><strong>ASR</strong> (service: opea/whisper-gaudi, model: openai/whisper-small)</li>
                    <li><strong>LLM 'text-generation'</strong> (service: opea/llm-textgen, model: Intel/neural-chat-7b-v3-3)</li>
                    <li><strong>TTS</strong> (service: opea/speecht5-gaudi, model: microsoft/speecht5_tts)</li>
                    <li><strong>Animation</strong> (service: opea/animation, model: wav2lip+gfpgan)</li>
                </ul></p>
                        """
            )
        with gr.Row():
            gr.Image("assets/img/flowchart.png", label="Megaservice Flowchart")
        with gr.Row():
            gr.Markdown(
                """
            <p style='font-size: 24px;'>The AI Avatar Audio Chatbot is powered by the following Intel® AI software:<br>
                        <ul style='font-size: 24px;'>
                        <li><strong>Intel Gaudi Software v1.17.0</strong></li>
                        <li><strong>PyTorch v2.3.1 (Eager mode + torch.compile) </strong></li>
                        <li><strong>HPU Graph</strong></li>
                        <li><strong>Intel Neural Compressor (INC)</strong></li>
                        </ul></p>
                        """
            )

        # Disclaimer
        gr.Markdown("<hr>")  # Divider
        gr.Markdown("<h2 style='font-size: 24px;'>Notices & Disclaimers</h1>")
        gr.Markdown(
            """
                    <p style='font-size: 20px;'>Intel is committed to respecting human rights and avoiding complicity in human rights abuses. See Intel's Global Human Rights Principles. Intel's products and software are intended only to be used in applications that do not cause or contribute to a violation of an internationally recognized human right.<br></p>
                    <p style='font-size: 20px;'>© Intel Corporation.  Intel, the Intel logo, and other Intel marks are trademarks of Intel Corporation or its subsidiaries.  Other names and brands may be claimed as the property of others.<br></p>
                    <p style='font-size: 20px;'>You may not use or facilitate the use of this document in connection with any infringement or other legal analysis concerning Intel products described herein. You agree to grant Intel a non-exclusive, royalty-free license to any patent claim thereafter drafted which includes subject matter disclosed herein.<br></p>
                    """
        )

        # State transitions
        # for i in range(len(image_pils)):
        #     image_click_buttons[i].click(
        #         update_selected_image_state, inputs=[gr.Number(value=i, visible=False)], outputs=[face_input]
        #     )
        # for i in range(len(video_paths)):
        #     video_click_buttons[i].click(
        #         update_selected_image_state,
        #         inputs=[gr.Number(value=i + len(image_pils), visible=False)],
        #         outputs=[face_input],
        #     )
        submit_button.click(
            initial_process,
            inputs=[audio_input, face_input, model_choice],
            outputs=[
                video_output,
                video_time_text,
            ],
        )

        demo.queue().launch(server_name="0.0.0.0", server_port=7861)
