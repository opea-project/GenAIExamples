# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


FROM nginx:alpine

RUN apk add --no-cache gettext

COPY comps/nginx/docker/nginx.conf.template /etc/nginx/nginx.conf.template

ENV FRONTEND_SERVICE_IP=localhost
ENV FRONTEND_SERVICE_PORT=5173
ENV BACKEND_SERVICE_NAME=chatqna
ENV BACKEND_SERVICE_IP=localhost
ENV BACKEND_SERVICE_PORT=8888

COPY comps/nginx/docker/start-nginx.sh /usr/local/bin/start-nginx.sh
RUN chmod +x /usr/local/bin/start-nginx.sh

CMD ["/usr/local/bin/start-nginx.sh"]
