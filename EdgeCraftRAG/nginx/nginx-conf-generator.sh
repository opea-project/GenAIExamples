#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 DP_NUM output-file-path"
    exit 1
fi

# Get the port number from the command line argument
PORT_NUM=$1

# Start generating the Nginx configuration
cat <<EOL > $2
worker_processes  auto;
events {
    worker_connections  1024;
}
http {

    upstream multi-arc-serving-container {
EOL

# Generate the server lines
for ((i=0; i<PORT_NUM; i++)); do
    PORT_VAR="VLLM_SERVICE_PORT_$i"
    echo "        server ${HOST_IP}:${!PORT_VAR:-8$((i+1))00};" >> $2
done

# Close the upstream block and the http block
cat <<EOL >> $2
    }
    include /etc/nginx/mime.types;
    default_type  application/octet-stream;
    client_max_body_size 50M;
    sendfile on;

    keepalive_timeout  65;
    keepalive_requests 1000;
    server {
        listen 8086;
        server_name _;
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            add_header Cache-Control "no-cache";
            try_files $uri $uri/ /index.html;
        }
        location /v1/completions {
            proxy_pass http://multi-arc-serving-container/v1/completions;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
        location /metrics {
            proxy_pass http://multi-arc-serving-container/metrics;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        location ~ /\. {
            deny all;
        }
    }
}
EOL

echo "Nginx configuration generated in nginx.conf"
