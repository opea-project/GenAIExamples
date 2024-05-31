#!/bin/bash


docker build . -t translation:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
