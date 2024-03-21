#!/bin/bash

docker build . -t document-summarize:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
