#!/bin/bash



docker build . -t intel/gen-ai-examples:copilot --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
