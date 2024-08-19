# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


FROM nginx:alpine

RUN apk add --no-cache gettext

COPY nginx.conf.template /etc/nginx/nginx.conf.template

ENV FRONTEND_SERVICE_IP=localhost
ENV FRONTEND_SERVICE_PORT=5173
ENV BACKEND_SERVICE_NAME=chatqna
ENV BACKEND_SERVICE_IP=localhost
ENV BACKEND_SERVICE_PORT=8888

CMD /bin/sh -c "envsubst '${FRONTEND_SERVICE_IP} ${FRONTEND_SERVICE_PORT} ${BACKEND_SERVICE_NAME} ${BACKEND_SERVICE_IP} ${BACKEND_SERVICE_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
