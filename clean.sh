#!/bin/bash

# Define processes to kill
processes=( "ffmpeg" "gunicorn" "transcript" )

# Loop through each process
for process in "${processes[@]}"; do
  # Use ps to find matching process IDs
  pids=$(ps -ef | grep -v grep | grep "$process" | awk '{print $2}')

  # Check if any PIDs found
  if [[ ! -z "$pids" ]]; then
    echo "Terminating $process..."
    # Kill each process using kill
    for pid in $pids; do
      kill $pid
    done
  else
    echo "No $process processes found."
  fi
done

# Clean old files (older than RETENTION_DAYS)
RETENTION_DAYS=${RETENTION_DAYS:-7}
OUTPUT_DIR=${OUTPUT_DIR:-./output}

echo "Cleaning files older than $RETENTION_DAYS days in $OUTPUT_DIR..."
find "$OUTPUT_DIR" -type f \( -name "*.mkv" -o -name "*.m4a" -o -name "*.txt" \) -mtime +$RETENTION_DAYS -delete

echo "Done!"