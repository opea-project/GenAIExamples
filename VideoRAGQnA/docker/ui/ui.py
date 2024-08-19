from io import BytesIO
import json
import os
import requests
import time
import streamlit as st
# import threading


MEGA_SERVICE_URL = "http://localhost:5031/v1/lvm"
VIDEO_DIR = "./data"

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)
   
def download_video(url):
    """Download video from URL and return as bytes."""
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        st.error(f"Failed to download video. Status code: {response.status_code}")
        return None

def play_video(url, offset):
    """Play video from URL with specified offset."""
    with st.spinner('获取视频流...'):
        video_bytes = download_video(url)
    if video_bytes:
        st.video(video_bytes, start_time=int(offset))
        
def clear_chat_history():
    st.session_state.example_video = 'Enter Text'
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

st.set_page_config(initial_sidebar_state='collapsed', layout='wide')
st.title("Video RAG")
title_alignment="""
<style>
h1 {
  text-align: center
}

video.stVideo {
    width: 200px;
    height: 500px;      
}
</style>
"""
st.markdown(title_alignment, unsafe_allow_html=True)

if 'llm' not in st.session_state.keys():
    with st.spinner('Loading Models . . .'):
        time.sleep(1)
 
        print("Check health of the megaservice . . .")
        # st.session_state['llm'] = VideoLLM()
        # TODO

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]


st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

if 'prevprompt' not in st.session_state.keys():
    st.session_state['prevprompt'] = ''
    print("Setting prevprompt to None")
if 'prompt' not in st.session_state.keys():
    st.session_state['prompt'] = ''
# Disable since no support for similar video
# if 'qcnt' not in st.session_state.keys():
#     st.session_state['qcnt'] = 0

def handle_message():
    params = None
    full_response = ""
    
    print("-"*30)
    print("starting message handling")
    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        # Handle user messages here
        with st.chat_message("assistant"):
            placeholder = st.empty()
            start = time.time()
            prompt = st.session_state['prompt']
            
            if prompt == 'Find similar videos':
                prompt = st.session_state['prevprompt']
                # st.session_state['qcnt'] += 1
            else:
                # st.session_state['qcnt'] = 0
                st.session_state['prevprompt'] = prompt
            
            # TODO: request the megaservice, get the answer: request(prompt)
            try:
                response = requests.post(MEGA_SERVICE_URL,
                    json={
                        "video_url": "https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4",
                        "chunk_start": 0,
                        "chunk_duration": 7,
                        "prompt": "what is the girl doing",
                        "max_new_tokens": 100
                    },
                    proxies={"http": None},
                    stream=True
                )
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        if params is None:
                            try:
                                chunk_str = chunk.decode('utf-8').replace("'", '"')
                                params = json.loads(chunk_str)
                                
                                video_url = params['video_url']
                                chunk_start = params['chunk_start']
                                print("VIDEO NAME USED IN PLAYBACK: ", video_url) 
                                
                                video_name = video_url.split('/')[-1]
                                full_response += f"Most relevant retrived video is **{video_name}** \n\n"
                                
                                # play_video
                                # threading.Thread(target=play_video, args=(video_url, chunk_start)).start()
                                with col2:
                                    play_video(video_url, chunk_start)
                                
                            except json.JSONDecodeError:
                                print("In the param decode error branch")
                                print(chunk.decode('utf-8'))
                        else:
                            new_text = chunk.decode('utf-8')
                            print(new_text, end=" ", flush=True)
                            full_response += new_text
                            placeholder.markdown(full_response)
                
            except requests.HTTPError as http_err:
                st.error(f"HTTP error occurred: {http_err}")
            except requests.RequestException as req_err:
                st.error(f"Error occurred: {req_err}")
            except Exception as err:
                st.error(f"An unexpected error occurred: {err}")

            end = time.time()
            full_response += f'\n\n🚀 Generated in {(end - start):.4f} seconds.'
            #chat_state, img_list = chat_reset(chat_state, img_list)
            #chat.clear()
            placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        print("-"*30)
        print("message handling done")
        st.session_state.messages.append(message)
      
def display_messages():
    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

col1, col2 = st.columns([2, 1])

with col1:
    st.selectbox(
        'Example Prompts',
        (
            'Enter Text', 
            'Man wearing glasses', 
            'People reading item description',
            'Man holding red shopping basket',
            'Was there any person wearing a blue shirt seen today?',
            'Was there any person wearing a blue shirt seen in the last 6 hours?',
            'Was there any person wearing a blue shirt seen last Sunday?',
            'Was a person wearing glasses seen in the last 30 minutes?',
            'Was a person wearing glasses seen in the last 72 hours?',
        ),
        key='example_video'
    )

    st.write('You selected:', st.session_state.example_video)

if st.session_state.example_video == 'Enter Text':
    if prompt := st.chat_input(disabled=False):
        st.session_state['prompt'] = prompt
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
        if prompt == 'Find similar videos':            
            st.session_state.messages.append({"role": "assistant", "content": "Not supported"})
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
else:
    prompt = st.session_state.example_video
    st.session_state['prompt'] = prompt
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    st.chat_input(disabled=True)
    if prompt == 'Find similar videos':
        st.session_state.messages.append({"role": "user", "content": prompt+': '+st.session_state['prevprompt']})
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})

with col1:
    display_messages()
    handle_message()