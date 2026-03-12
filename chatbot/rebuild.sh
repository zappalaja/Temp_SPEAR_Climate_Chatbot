#!/bin/bash
# SPEAR Climate Chatbot - Rebuild Script (Podman)

echo "🔄 Rebuilding SPEAR Climate Chatbot..."

echo "🛑 Stopping current container..."
podman stop spear-chatbot 2>/dev/null
podman rm spear-chatbot 2>/dev/null

echo "🗑️  Removing old image..."
podman rmi spear-chatbot 2>/dev/null

echo "🔨 Rebuilding Podman image..."
podman build --no-cache -t spear-chatbot .

echo "▶️  Starting updated container..."
source .env
podman run -d \
    --name spear-chatbot \
    -p 8501:8501 \
    --env-file .env \
    --restart unless-stopped \
    spear-chatbot

# Wait a moment for container to start
sleep 3

# Check if container is running
if podman ps --format "{{.Names}}" | grep -q "^spear-chatbot$"; then
    echo ""
    echo "✅ Chatbot rebuilt and restarted!"
    echo "🌐 Opening browser to: http://localhost:8501"
    
    # Automatically open browser (try common browsers)
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:8501 >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open http://localhost:8501 >/dev/null 2>&1 &
    elif command -v firefox >/dev/null 2>&1; then
        firefox http://localhost:8501 >/dev/null 2>&1 &
    elif command -v google-chrome >/dev/null 2>&1; then
        google-chrome http://localhost:8501 >/dev/null 2>&1 &
    else
        echo "🔗 Please manually open: http://localhost:8501"
    fi
else
    echo ""
    echo "❌ Failed to start container. Check logs with:"
    echo "   podman logs spear-chatbot"
    exit 1
fi
