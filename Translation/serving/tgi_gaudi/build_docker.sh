#!/bin/bash

docker build . -t tgi-gaudi-translation:1.2.1 --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
