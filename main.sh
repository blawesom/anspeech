#!/bin/bash

gunicorn -b 0.0.0.0 flask_server:app --capture-output --log-file output.log &

mkdir -p output
cd output

# anstream to flask serv
# nohup setsid bash -c "../anstream.sh $1 >> stream.log &" 

nohup setsid bash -c "../antranscript.sh >> transcript.log &"

# echo -e "\nStream and transcript started at $(date +"%H:%M:%S")\n"

# ps aux --forest | grep "/bin/bash"