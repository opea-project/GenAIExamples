#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# Reference: https://github.com/gasse/webarena-setup

# stop if any error occur
set -e

BASE_DIR=`dirname "${BASH_SOURCE[0]}"`
source ${BASE_DIR}/set_env.sh

assert() {
  if ! "$@"; then
    echo "Assertion failed: $*" >&2
    exit 1
  fi
}

load_docker_image() {
  local IMAGE_NAME="$1"
  local INPUT_FILE="$2"

  if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}:"; then
    echo "Loading Docker image ${IMAGE_NAME} from ${INPUT_FILE}"
    docker load --input "${INPUT_FILE}"
  else
    echo "Docker image ${IMAGE_NAME} is already loaded."
  fi
}

start() {
    # Verify that the docker image archive file exists
  assert [ -f ${ARCHIVES_LOCATION}/shopping_admin_final_0719.tar ]

  # Load image
  load_docker_image "shopping_admin_final_0719" ${ARCHIVES_LOCATION}/shopping_admin_final_0719.tar

  # Create and run the container
  docker create --name shopping_admin_server -p ${SHOPPING_ADMIN_PORT}:80 shopping_admin_final_0719

  # Start the container
  docker start shopping_admin_server
  echo -n -e "Waiting 60 seconds for all services to start..."
  sleep 60
  echo -n -e " done\n"

  echo -n -e "Configuring Magento settings inside the container..."
  docker exec shopping_admin_server php /var/www/magento2/bin/magento config:set admin/security/password_is_forced 0
  docker exec shopping_admin_server php /var/www/magento2/bin/magento config:set admin/security/password_lifetime 0
  docker exec shopping_admin_server /var/www/magento2/bin/magento setup:store-config:set --base-url="http://${PUBLIC_HOSTNAME}:${SHOPPING_ADMIN_PORT}"
  docker exec shopping_admin_server mysql -u magentouser -pMyPassword magentodb -e  "UPDATE core_config_data SET value='http://$PUBLIC_HOSTNAME:$SHOPPING_ADMIN_PORT/' WHERE path = 'web/secure/base_url';"
  docker exec shopping_admin_server /var/www/magento2/bin/magento cache:flush
  echo -n -e " done\n"
}

stop() {
  docker stop shopping_admin_server || true
  docker rm shopping_admin_server || true
}

case "$1" in
    start)
        echo "Starting shopping_admin server..."
        start
        echo "shopping_admin server started."
        ;;
    stop)
        echo "Stopping shopping_admin server..."
        stop
        echo "shopping_admin server stopped."
        ;;
    restart)
        echo "Restarting shopping_admin server..."
        stop
        sleep 2
        start
        echo "shopping_admin server restarted."
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
