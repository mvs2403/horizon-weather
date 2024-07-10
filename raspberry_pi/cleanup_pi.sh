#!/bin/bash
# Stop and remove Docker containers
docker-compose down

# Remove Docker images
docker rmi $(docker images -q)