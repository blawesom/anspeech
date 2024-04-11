#!/bin/bash

source venv/bin/activate


while true; do
  today=$(date +"%d-%m-%Y")
  pattern="an-${today}_*.mkv"
  timestamp=`date "+%Y-%m-%d %H:%M:%S"`  
  for file in $pattern_*.mkv; do
    if [[ ! $(lsof "$file" | grep -vE "^COMMAND.+PID" | wc -l) -gt 0 ]]; then
      if [[ ! -f "${file%mkv}txt" ]]; then
        echo -e "$timestamp New segment found, running audio conversion..."
        ffmpeg -i $file -map 0:1 -c copy "${file%mkv}m4a"
        echo -e "$timestamp Conversion completed, running transcription..."
        whisper "${file%mkv}m4a" --model medium --language fr --output_format txt
        echo -e "$timestamp Transcription completed."
      else
        echo -e "$timestamp Skipping TXT file for $file already exists"
        sleep 1
      fi
    else
      echo -e "$timestamp Skipping: $file is opened"
      sleep 10
    fi
  done
done