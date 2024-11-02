#!/bin/bash

# keeping existing certs
echo "Pulling all container images and orchestrating with docker-compose"

# bring everything up (pull all images)
docker-compose up -d
