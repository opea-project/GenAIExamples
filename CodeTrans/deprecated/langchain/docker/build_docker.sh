#!/bin/bash


docker build . -t intel/gen-ai-examples:code-translation --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
