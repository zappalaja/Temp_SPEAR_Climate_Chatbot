#!/usr/bin/env bash
#
# Run the SPEAR Earth System Data Assistant container.
#
# Usage: ./run-container.sh
#
# API keys are read from chatbot/.env (never baked into the image).
# ChromaDB and merged markdown are volume-mounted from the project.
#

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="spear-earth-system-data-assistant"
CONTAINER_NAME="spear-assistant"

# Paths to mount
CHROMA_DB="$PROJECT_DIR/rag-service/ingestion/chroma_db"
MERGED_MD="$PROJECT_DIR/rag-service/ingestion/nougat_merged_md"
ENV_FILE="$PROJECT_DIR/chatbot/.env"

# Validate prerequisites
if ! podman image exists "$IMAGE"; then
    echo "Image not found: $IMAGE"
    echo "Build it first:  podman build -t $IMAGE -f Containerfile ."
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing: $ENV_FILE"
    echo "Copy chatbot/.env.example to chatbot/.env and add your API keys."
    exit 1
fi

# Stop existing container if running
if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping existing container..."
    podman stop "$CONTAINER_NAME" 2>/dev/null || true
    podman rm "$CONTAINER_NAME" 2>/dev/null || true
fi

echo "Starting $IMAGE..."
podman run \
    --name "$CONTAINER_NAME" \
    --env-file "$ENV_FILE" \
    -v "$CHROMA_DB:/app/chroma_db" \
    -v "$MERGED_MD:/app/nougat_merged_md" \
    -p 8501:8501 \
    "$IMAGE"
