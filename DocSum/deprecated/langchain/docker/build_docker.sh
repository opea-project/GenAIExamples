#!/bin/bash


docker build . -t intel/gen-ai-examples:document-summarize --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
