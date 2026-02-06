#!/bin/bash

# Resolve script directory so we can call transcribe.py by absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment if .env exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
fi

# Activate virtualenv if it exists (legacy path kept for compatibility)
if [[ -f "../../whisper-env/bin/activate" ]]; then
  source ../../whisper-env/bin/activate
fi

while true; do
  today=$(date +"%d-%m-%Y")
  timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  for file in *.mkv; do
    echo -e "$timestamp Looking for $file..."
    if [[ -f "$file" ]]; then
      if [[ ! $(lsof "$file" | grep -vE "^COMMAND.+PID" | wc -l) -gt 0 ]]; then
        if [[ ! -f "${file%mkv}txt" ]]; then
          if [[ ! -f "${file%mkv}m4a" ]]; then
            echo -e "$timestamp New segment found, running audio conversion..."
            ffmpeg -i "$file" -map 0:1 -c copy "${file%mkv}m4a" -y
            echo -e "$timestamp Conversion completed, running transcription..."
          else
            echo -e "$timestamp Skipping M4A conversion for $file already exists"
            echo -e "$timestamp Running transcription..."
          fi
          python "$SCRIPT_DIR/transcribe.py" "${file%mkv}m4a"
          echo -e "$timestamp Transcription completed."
          cat *.txt > "$today.txt"
          echo -e "$timestamp Output concatenated into $today.txt."
          s3cmd put "$today.txt" s3://public/
          echo -e "$timestamp New file $today.txt published."
          s3cmd setacl "s3://public/$today.txt" --acl-public
          echo -e "$timestamp https://oos.eu-west-2.outscale.com/public/$today.txt is now public."
          rm "$today.txt"
        else
          echo -e "$timestamp Skipping TXT transcription for $file already exists"
          sleep 1
        fi
      else
        echo -e "$timestamp Skipping: $file is opened"
        sleep 10
      fi
    fi
    sleep 1
  done
done
