FROM langchain/langchain

ARG http_proxy
ARG https_proxy
ENV http_proxy=$http_proxy
ENV https_proxy=$https_proxy

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        libgl1-mesa-glx \
        libjemalloc-dev

RUN pip install --upgrade pip \
    sentence-transformers \
    langchain-cli \
    pydantic==1.10.13 \
    langchain==0.1.12 \
    poetry \
    langchain_benchmarks \
    pyarrow \
    jupyter \
    docx2txt \
    pypdf \
    beautifulsoup4 \
    python-multipart \
    intel-extension-for-pytorch \
    intel-openmp

ENV PYTHONPATH=/ws:/summarize-app/app

COPY summarize-app /summarize-app
WORKDIR /summarize-app

CMD ["/bin/bash"]
