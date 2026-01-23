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
fi

# Restart service if using systemd
if systemctl is-active --quiet anspeech; then
    sudo systemctl restart anspeech
    echo "Service restarted"
else
    echo "Start service with: ./main.sh"
fi

echo "Deployment complete!"
