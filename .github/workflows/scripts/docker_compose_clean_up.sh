#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# The test machine used by several opea projects, so the test scripts can't use `docker compose down` to clean up
# the all the containers, ports and networks directly.
# So we need to use the following script to minimize the impact of the clean up.

flag=${test_case%_on_*}
flag=${flag#test_}
yaml_file=$(find . -type f -wholename "*${hardware}/${flag}.yaml")
echo $yaml_file

case "$1" in
    containers)
        echo "Stop and remove all containers used by the services in $yaml_file ..."
        containers=$(cat $yaml_file | grep container_name | cut -d':' -f2)
        for container_name in $containers; do
            cid=$(docker ps -aq --filter "name=$container_name")
            if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
        done
        ;;
    ports)
        # Remove all ports used by containers
        echo "Release all ports used by the services in $yaml_file ..."
        pip install jq yq
        which pip
        which python
        echo "$PATH"
        ports=$(yq '.services[].ports[] | split(":")[0]' $yaml_file | grep -o '[0-9]\+')
        echo "$ports"
        for port in $ports; do
          cid=$(docker ps --filter "publish=${port}" --format "{{.ID}}")
          if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
        done
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
