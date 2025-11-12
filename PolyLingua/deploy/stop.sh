#!/bin/bash
# Copyright (C) 2024
# SPDX-License-Identifier: Apache-2.0

set -e

echo "======================================"
echo "Stopping OPEA PolyLingua Service"
echo "======================================"

echo ""
echo "Stopping services..."
docker compose down

echo ""
echo "======================================"
echo "Services stopped successfully!"
echo "======================================"
echo ""
echo "To start services again:"
echo "  ./deploy/start.sh"
echo ""
echo "To remove all data (including model cache):"
echo "  docker compose down -v"
echo ""
