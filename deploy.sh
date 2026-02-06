#!/bin/bash
set -e

echo "Deploying AnSpeech..."

# Pull latest changes
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p output web

# Copy .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please configure it"
    echo "IMPORTANT: Set HF_TOKEN in .env for speaker diarization (requires Hugging Face token)"
fi

# Validate diarization config
source .env 2>/dev/null || true
if [ "${DIARIZATION_ENABLED:-true}" = "true" ] && [ -z "$HF_TOKEN" ]; then
    echo ""
    echo "WARNING: Diarization is enabled but HF_TOKEN is not set."
    echo "  - Set HF_TOKEN in .env with your Hugging Face access token"
    echo "  - Accept the pyannote model license at https://huggingface.co/pyannote/speaker-diarization-3.1"
    echo "  - Or set DIARIZATION_ENABLED=false to disable diarization"
    echo ""
fi

# Restart service if using systemd
if systemctl is-active --quiet anspeech; then
    sudo systemctl restart anspeech
    echo "Service restarted"
else
    echo "Start service with: ./main.sh"
fi

echo "Deployment complete!"
