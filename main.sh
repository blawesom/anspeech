#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
fi

echo "Starting AnSpeech..."
echo "  Diarization: ${DIARIZATION_ENABLED:-true}"
if [ "${DIARIZATION_ENABLED:-true}" = "true" ] && [ -z "$HF_TOKEN" ]; then
  echo "  WARNING: HF_TOKEN not set - diarization will be disabled at runtime"
fi

gunicorn -b 0.0.0.0 flask_server:app --capture-output --log-file gunicorn.log &

mkdir -p output
cd output

# anstream to flask serv
# nohup setsid bash -c "../anstream.sh $1 >> stream.log &"

nohup setsid bash -c "../antranscript.sh >> transcript.log &"

echo "AnSpeech started at $(date +"%H:%M:%S")"
