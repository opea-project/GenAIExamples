#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Robust Docker cleanup function for CI/CD
# Handles network removal errors by ensuring containers are stopped first

set -e

COMPOSE_FILE="${1:-docker-compose.yml}"
COMPOSE_DIR="${2:-.}"

function stop_docker() {
    echo "Stopping Docker services..."

    cd "$COMPOSE_DIR" || exit 1

    # Step 1: Stop all containers gracefully
    echo "Step 1: Stopping containers..."
    docker compose -f "$COMPOSE_FILE" stop 2>/dev/null || {
        echo "Warning: Some containers may not have stopped"
        # Force stop any running containers
        docker compose -f "$COMPOSE_FILE" ps -q | xargs -r docker stop 2>/dev/null || true
    }

    # Step 2: Wait for containers to fully stop
    echo "Step 2: Waiting for containers to stop..."
    sleep 5

    # Step 3: Remove containers
    echo "Step 3: Removing containers..."
    docker compose -f "$COMPOSE_FILE" rm -f 2>/dev/null || {
        echo "Warning: Some containers may not have been removed"
        # Force remove any remaining containers
        docker compose -f "$COMPOSE_FILE" ps -aq | xargs -r docker rm -f 2>/dev/null || true
    }

    # Step 4: Remove volumes and networks (with retry logic)
    echo "Step 4: Removing volumes and networks..."
    for attempt in {1..3}; do
        if docker compose -f "$COMPOSE_FILE" down -v 2>/dev/null; then
            echo "Successfully removed volumes and networks"
            break
        else
            echo "Attempt $attempt failed: Network may have active endpoints"

            # Get network names from compose file
            NETWORKS=$(docker compose -f "$COMPOSE_FILE" config --networks 2>/dev/null | grep -E "^\s+[a-zA-Z]" | awk '{print $1}' | tr -d ':') || true

            # Disconnect any remaining containers from networks
            for network in $NETWORKS; do
                echo "Disconnecting containers from network: $network"
                CONTAINERS=$(docker network inspect "$network" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || true)
                for container in $CONTAINERS; do
                    docker network disconnect -f "$network" "$container" 2>/dev/null || true
                done
            done

            # Wait before retry
            sleep 5
        fi
    done

    # Step 5: Final cleanup - remove orphaned containers and networks
    echo "Step 5: Final cleanup..."

    # Remove any containers that might be orphaned
    docker ps -a --filter "label=com.docker.compose.project" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true

    # Remove networks that might be orphaned (be careful with this)
    docker network ls --filter "name=opea\|cogniware\|xeon\|gaudi" --format "{{.ID}}" | while read -r net_id; do
        # Check if network has any endpoints
        if [ -z "$(docker network inspect "$net_id" --format '{{range .Containers}}{{.Name}}{{end}}' 2>/dev/null)" ]; then
            docker network rm "$net_id" 2>/dev/null || true
        fi
    done

    echo "Docker cleanup completed"
}

# If script is run directly, execute stop_docker
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    stop_docker "$@"
fi
