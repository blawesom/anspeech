#!/bin/bash

# Check if a playlist argument is provided
if [ $# -eq 0 ]; then
  echo "Error: Please provide a playlist file as an argument."
  exit 1
fi

mkdir -p output
cd output

# TODO: correct nohup out error for anstream.sh
nohup setsid bash -c "../anstream.sh $1 >> stream.log &" &
nohup setsid bash -c "../antranscript.sh >> transcript.log &" &

echo -e "\nStream and transcript started at $(date +"%H:%M:%S")\n"

ps aux --forest | grep "/bin/bash"