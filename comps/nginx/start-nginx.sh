# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#!/bin/sh
envsubst '${FRONTEND_SERVICE_IP} ${FRONTEND_SERVICE_PORT} ${BACKEND_SERVICE_NAME} ${BACKEND_SERVICE_IP} ${BACKEND_SERVICE_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
