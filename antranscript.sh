#!/bin/bash

source venv/bin/activate

while true; do
  today=$(date +"%d-%m-%Y")
  pattern="an-${today}_*.mkv"
  
  for file in $pattern_*.mkv; do
    if [[ ! $(lsof "$file" | grep -vE "^COMMAND.+PID" | wc -l) -gt 0 ]]; then
      if [[ ! -f "${file%mkv}txt" ]]; then
        echo -e "\n\nNew segment found, running audio conversion..."
        ffmpeg -i $file -map 0:1 -c copy "${file%mkv}m4a"
        echo -e "\n\nConversion completed, running transcription..."
        whisper "${file%mkv}m4a" --model medium --language fr --output_format txt
        echo -e "\n\nTranscription completed."
      else
        echo -e "\n\nSkipping: TXT file for $file already exists"
        sleep 1
      fi
    else
      echo -e "\n\nSkipping: $file is opened"
      sleep 10
    fi
  done
done