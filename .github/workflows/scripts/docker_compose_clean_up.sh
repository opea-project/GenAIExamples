#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# The test machine used by several opea projects, so the test scripts can't use `docker compose down` to clean up
# the all the containers, ports and networks directly.
# So we need to use the following script to minimize the impact of the clean up.

test_case=${test_case:-"test_compose_on_gaudi.sh"}
hardware=${hardware:-"gaudi"}
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
            if [[ -n "$cid" ]]; then docker stop "$cid" && docker rm "$cid" && sleep 1s; fi
        done
        ;;
    ports)
        echo "Release all ports used by the services in $yaml_file ..."
        pip install jq==1.10.0 yq==3.4.3
        ports=$(yq '.services[].ports[] | split(":")[0]' $yaml_file | grep -o '[0-9a-zA-Z_-]\+')
        echo "All ports list..."
        echo "$ports"
        for port in $ports; do
          if [[ $port =~ [a-zA-Z_-] ]]; then
            echo "Search port value $port from the test case..."
            port_fix=$(grep -E "export $port=" tests/$test_case | cut -d'=' -f2)
            if [[ "$port_fix"  ]]; then
               port=$port_fix
            fi
          fi
          if [[ $port =~ [0-9] ]]; then
            if [[ $port == 5000 ]]; then
              echo "Error: Port 5000 is used by local docker registry, please DO NOT use it in docker compose deployment!!!"
              exit 1
            fi
            echo "Check port $port..."
            cid=$(docker ps --filter "publish=${port}" --format "{{.ID}}")
            if [[ -n "$cid" ]]; then docker stop "$cid" && docker rm "$cid" && echo "release $port"; fi
          fi
        done
        ;;
    *)
        echo "Unknown function: $1"
        ;;
esac
