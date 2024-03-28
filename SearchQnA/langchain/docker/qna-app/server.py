import os

from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.retrievers.web_research import WebResearchRetriever
from langchain.chains import RetrievalQAWithSourcesChain
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_community.llms import HuggingFaceEndpoint
from starlette.middleware.cors import CORSMiddleware
from langchain.callbacks.base import BaseCallbackHandler

from queue import Queue
from threading import Thread
import sys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueueCallbackHandler(BaseCallbackHandler):
    """A queue that holds the result answer token buffer for streaming response.
    """

    def __init__(self, queue: Queue):
        self.queue = queue
        self.enter_answer_phase = False

    def on_llm_new_token(self, token: str, **kwargs):
        sys.stdout.write(token)
        sys.stdout.flush()
        if self.enter_answer_phase:
            self.queue.put(
                {
                    "answer": token,
                }
            )

    def on_llm_end(self, *args, **kwargs):
        self.enter_answer_phase = not self.enter_answer_phase
        return True


class SearchQuestionAnsweringAPIRouter(APIRouter):
    """The router for SearchQnA example.

    The input request will firstly go through Google Search, and the fetched HTML will be stored in the vector db.
    Then the input request together with relevant retrieved documents will be forward to the LLM to get the answers.
    """

    def __init__(
        self,
        entrypoint: str,
        vectordb_embedding_model: str = "hkunlp/instructor-large",
        vectordb_persistent_directory: str = "./chroma_db_oai"
    ) -> None:
        super().__init__()
        self.entrypoint = entrypoint
        self.queue = Queue()  # For streaming output tokens

        # setup TGI endpoint
        self.llm = HuggingFaceEndpoint(
            endpoint_url=entrypoint,
            max_new_tokens=256,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
            streaming=True,
            callbacks=[QueueCallbackHandler(queue=self.queue)],
        )

        # check google api key is provided
        if not "GOOGLE_API_KEY" in os.environ or not "GOOGLE_API_KEY" in os.environ:
            raise Exception("Please make sure to set GOOGLE_API_KEY and GOOGLE_API_KEY environment variables!")

        # Notice: please check or manually delete the vectordb directory if you do not previous histories
        self.vectorstore = Chroma(
            embedding_function=HuggingFaceInstructEmbeddings(
                model_name=vectordb_embedding_model
            ),
            persist_directory=vectordb_persistent_directory,
        )

        # Build up the google search service
        self.search = GoogleSearchAPIWrapper()

        # Compose the websearch retriever
        self.web_search_retriever = WebResearchRetriever.from_llm(
            vectorstore=self.vectorstore, llm=self.llm, search=self.search
        )

        # Compose the whole chain
        self.llm_chain = RetrievalQAWithSourcesChain.from_chain_type(
            self.llm,
            retriever=self.web_search_retriever,
        )

    def handle_search_chat(self, query: str):
        response = self.llm_chain({"question": query})
        return response["answer"], response["sources"]


tgi_endpoint = os.getenv("TGI_ENDPOINT", "http://localhost:8083")

router = SearchQuestionAnsweringAPIRouter(
    entrypoint=tgi_endpoint,
)


@router.post("/v1/rag/web_search_chat")
async def web_search_chat(request: Request):
    params = await request.json()
    print(f"[websearch - chat] POST request: /v1/rag/web_search_chat, params:{params}")
    query = params["query"]
    answer, sources = router.handle_search_chat(query=query)
    print(f"[websearch - chat] answer: {answer}, sources: {sources}")
    return {"answer": answer, "sources": sources}


@router.post("/v1/rag/web_search_chat_stream")
async def web_search_chat_stream(request: Request):
    params = await request.json()
    print(
        f"[websearch - streaming chat] POST request: /v1/rag/web_search_chat_stream, params:{params}"
    )
    query = params["query"]

    def stream_callback(query):
        finished = object()

        def task():
            _ = router.llm_chain({"question": query})
            router.queue.put(finished)

        t = Thread(target=task)
        t.start()
        while True:
            try:
                item = router.queue.get()
                if item is finished:
                    break
                yield item
            except Queue.Empty:
                continue

    def stream_generator():
        chat_response = ""
        # FIXME need to add the sources and chat_history
        for res_dict in stream_callback({"question": query}):
            text = res_dict["answer"]
            chat_response += text
            if text == " ":
                yield f"data: @#$\n\n"
                continue
            if text.isspace():
                continue
            if "\n" in text:
                yield f"data: <br/>\n\n"
            new_text = text.replace(" ", "@#$")
            yield f"data: {new_text}\n\n"
        chat_response = chat_response.split("</s>")[0]
        print(f"[rag - chat_stream] stream response: {chat_response}")
        yield f"data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
