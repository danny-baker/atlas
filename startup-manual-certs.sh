#!/bin/bash

# keeping existing certs
echo "Pulling container images and bringing them up..."

# bring everything up (pull all images)
docker-compose up -d
