from io import BytesIO
import json
import os
import requests
import time
import streamlit as st


BACKEND_SERVICE_ENDPOINT = os.getenv("BACKEND_SERVICE_ENDPOINT", "http://localhost:8888/v1/videoragqna")
BACKEND_HEALTH_CHECK_ENDPOINT = os.getenv("BACKEND_HEALTH_CHECK_ENDPOINT", "http://localhost:8888/v1/health_check")


def perform_health_check():
    url = BACKEND_HEALTH_CHECK_ENDPOINT
    response = requests.get(url, headers={'accept': 'application/json'})
    return response
  
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
    with st.spinner('Loading Video ...'):
        video_bytes = download_video(url)
    if video_bytes:
        st.video(video_bytes, start_time=int(offset))
        
def clear_chat_history():
    st.session_state.example_video = 'Enter Text'
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

def handle_selectbox_change():
    prompt = st.session_state.example_video
    
    if prompt is not None:
        st.session_state['prompt'] = prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
    

def handle_chat_input():
    print("st.session_state.custom_prompt update", st.session_state.custom_prompt)
    prompt = st.session_state.custom_prompt

    st.session_state['prompt'] = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})

def handle_message(col):
    params = None
    full_response = ""

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        # Handle user messages here
        with st.chat_message("assistant"):
            placeholder = st.empty()
            start = time.time()
            prompt = st.session_state['prompt']
            request_data = {"messages": prompt, "stream": "True"}
            try:
                response = requests.post(BACKEND_SERVICE_ENDPOINT,
                    data=json.dumps(request_data),
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
                                placeholder.markdown(full_response)
                                
                                with col:
                                    play_video(video_url, chunk_start)
                                
                            except json.JSONDecodeError:
                                print("In the param decode error branch")
                                print(chunk.decode('utf-8'))
                        else:
                            new_text = chunk.decode('utf-8')
                            # print(new_text, end=" ", flush=True) 
                            full_response += new_text
                            placeholder.markdown(full_response)
                # Fake response
                # video_url = "https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4"
                # chunk_start=0
                # video_name = video_url.split('/')[-1]
                # full_response += f"Most relevant retrived video is **{video_name}** \n\n"
                # placeholder.markdown(full_response)
                # with col:
                #     play_video(video_url, chunk_start)
                # for i in range(10):
                #     full_response += f"new_text {i} "
                #     time.sleep(1)
                #     placeholder.markdown(full_response)
                    
                    
            except requests.HTTPError as http_err:
                st.error(f"HTTP error occurred: {http_err}")
            except requests.RequestException as req_err:
                st.error(f"Error occurred: {req_err}")
            except Exception as err:
                st.error(f"An unexpected error occurred: {err}")

            end = time.time()
            full_response += f'\n\n🚀 Generated in {(end - start):.4f} seconds.'
            placeholder.markdown(full_response)

        message = {"role": "assistant", "content": full_response}

        st.session_state.messages.append(message)
      
def display_messages():
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

def main():
    st.set_page_config(initial_sidebar_state='collapsed', layout='wide')
    st.title("Video RAG QnA")
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
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

    placeholder = st.empty()

    # check server health
    if "health_check" not in st.session_state.keys():
        with st.spinner('Checking health of the server...'):
            time.sleep(1)
            response = perform_health_check()
        if response.status_code == 200:
            placeholder.success('Server is healthy!', icon='✅')
            time.sleep(1) 
            placeholder.empty()  # Remove the message 
            st.session_state['health_check'] = True
        else:
            st.error(f'Server health check failed with status code {response.status_code}')
            st.stop()


    # Initialize conversation state
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    if 'prompt' not in st.session_state.keys():
        st.session_state['prompt'] = ''


    col1, col2 = st.columns([2, 1])
        
    with col1:
        st.selectbox(
            'Example Prompts',
            (
                'Man wearing glasses', 
                'People reading item description',
                'Man holding red shopping basket',
                'Was there any person wearing a blue shirt seen today?',
                'Was there any person wearing a blue shirt seen in the last 6 hours?',
                'Was there any person wearing a blue shirt seen last Sunday?',
                'Was a person wearing glasses seen in the last 30 minutes?',
                'Was a person wearing glasses seen in the last 72 hours?',
            ),
            key='example_video',
            index=None,
            placeholder="--- Options ---",
            on_change=handle_selectbox_change
        )
        
    st.chat_input(disabled=False, key='custom_prompt', on_submit=handle_chat_input)

    with col1:
        display_messages()
        handle_message(col2)

if __name__ == "__main__":
    main()