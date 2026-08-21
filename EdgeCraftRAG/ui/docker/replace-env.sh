#!/bin/sh

set -eu

NGINX_TEMPLATE="/etc/nginx/nginx.conf.template"
NGINX_CONF="/etc/nginx/nginx.conf"

: "${UI_SERVICE_PORT:=8082}"
: "${PIPELINE_SERVICE_HOST_IP:=edgecraftrag-server}"
: "${PIPELINE_SERVICE_PORT:=16010}"
: "${MEGA_SERVICE_HOST_IP:=ecrag}"
: "${MEGA_SERVICE_PORT:=16011}"

export UI_SERVICE_PORT
export PIPELINE_SERVICE_HOST_IP
export PIPELINE_SERVICE_PORT
export MEGA_SERVICE_HOST_IP
export MEGA_SERVICE_PORT

envsubst '${UI_SERVICE_PORT} ${PIPELINE_SERVICE_HOST_IP} ${PIPELINE_SERVICE_PORT} ${MEGA_SERVICE_HOST_IP} ${MEGA_SERVICE_PORT}' \
    < "$NGINX_TEMPLATE" \
    > "$NGINX_CONF"

if grep -n '\${[A-Za-z_][A-Za-z0-9_]*}' "$NGINX_CONF"; then
    echo "[replace-env] Unresolved nginx template variables remain in $NGINX_CONF" >&2
    exit 1
fi