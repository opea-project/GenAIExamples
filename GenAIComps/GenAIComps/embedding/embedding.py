import os
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from fastapi import APIRouter, FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


class EmbeddingRouter(APIRouter):

    def __init__(self, tei_endpoint=None) -> None:
        super().__init__()

        # Define LLM Chain
        if tei_endpoint:
            # create embeddings using TEI endpoint service
            self.embeddings = HuggingFaceHubEmbeddings(model=tei_endpoint)
        else:
            # create embeddings using local embedding model
            self.embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-large-en-v1.5")

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
router = EmbeddingRouter(tei_embedding_endpoint)

@router.post("/v1/embeddings")
async def rag_chat(request: Request):
    params = await request.json()
    print(f"[embeddings] POST request: /v1/embeddings, params:{params}")
    query = params["query"]

    embeddings = router.embeddings(query)
    return embeddings

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7000)