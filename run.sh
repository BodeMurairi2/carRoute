#!/usr/bin/env bash

IMAGE_NAME="bodemurairi2/carroute:v2"

echo "🔧 Building arm64 image and pushing to Docker Hub..."
sudo docker buildx build \
  --platform linux/arm64 \
  -t $IMAGE_NAME \
  --push \
  -f Dockerfile .

sudo docker pull $IMAGE_NAME

sleep 5

sudo docker rm -f carroute_test 2>/dev/null || true

sudo docker run -d --rm -p 80:8080 --name carroute_test $IMAGE_NAME
