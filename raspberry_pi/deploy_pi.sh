#!/bin/bash
# This script deploys the FastAPI application using Docker Compose:
# Navigate to the repository directory
cd "$(dirname "$0")"

# Run Docker Compose
docker-compose up --build -d