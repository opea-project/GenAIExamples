#!/bin/bash

docker build . -t qna-rag-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
