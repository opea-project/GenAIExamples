import gradio as gr
from fastapi import FastAPI
import uvicorn, os, requests, json, ast

app = FastAPI()
headers = {"Content-Type": "application/json"}

def generate_summary(text):
    global gateway_addr
    data = {
        "type": "text",
        "messages": text
    }
    
    print(gateway_addr)
    print(json.dumps(data))
    try:
        
        response = requests.post(
            url=gateway_addr,
            headers=headers,
            data=json.dumps(data),
            proxies={
                'http_proxy': os.environ['HTTP_PROXY'],
                'https_proxy': os.environ['HTTPS_PROXY']
            }
        )
        
        if response.status_code == 200:
            return response.text.replace("'\n\ndata: b'", "").replace("data: b' ", "").replace("</s>'\n\ndata: [DONE]\n\n","").replace("\n\ndata: b", "").replace("'\n\n", "").replace("'\n", "").replace('''\'"''' ,"")
                    
    except requests.exceptions.RequestException as e:
        return str(e)
    
    return str(response.status_code)

with gr.Blocks() as text_ui:
    with gr.Row():
        with gr.Column():
            input_text = gr.TextArea(label="Please paste content for summarization", placeholder="Paste the text information you need to summarize")
            submit_btn = gr.Button("Generate Summary")
        with gr.Column():
            generated_text = gr.TextArea(label="Text Summary", placeholder="Summarized text will be displayed here")
    submit_btn.click(
        fn=generate_summary,
        inputs=[input_text],
        outputs=[generated_text]
    )
with gr.Blocks() as demo:
    gr.Markdown(
        "# Doc Summary"
    )
    with gr.Tabs():
        with gr.TabItem("Paste Text"):
            text_ui.render()

demo.queue()
app = gr.mount_gradio_app(app, demo, path='/')



if __name__ == '__main__':
    backend_service_endpoint = os.getenv('BACKEND_SERVICE_ENDPOINT', "http://localhost:8888/v1/docsum")
    
    global gateway_addr
    gateway_addr = backend_service_endpoint
    
    uvicorn.run(app)