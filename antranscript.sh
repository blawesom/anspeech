#!/bin/bash

source ../../whisper-env/bin/activate

while true; do
  today=$(date +"%d-%m-%Y")
  pattern="an-${today}_*.mkv"
  timestamp=`date "+%Y-%m-%d %H:%M:%S"`
  for file in *.mkv; do
    echo -e "$timestamp Looking for $file..."
    if [[ -f "$file" ]]; then
      if [[ ! $(lsof "$file" | grep -vE "^COMMAND.+PID" | wc -l) -gt 0 ]]; then
        if [[ ! -f "${file%mkv}txt" ]]; then
          if [[ ! -f "${file%mkv}m4a" ]]; then
            echo -e "$timestamp New segment found, running audio conversion..."
            ffmpeg -i $file -map 0:1 -c copy "${file%mkv}m4a" -y
            echo -e "$timestamp Conversion completed, running transcription..."
            whisper "${file%mkv}m4a" --model medium --language fr --output_format txt
            echo -e "$timestamp Transcription completed."
          else
            echo -e "$timestamp Skipping M4A conversion for $file already exists"  
            echo -e "$timestamp Running transcription..."
            whisper "${file%mkv}m4a" --model medium --language fr --output_format txt
            echo -e "$timestamp Transcription completed."
          fi
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
