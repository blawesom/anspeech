#!/bin/bash

# Store the playlist filename from the argument
playlist_file="$1"

# Set your desired segment duration (in seconds)
segment_duration=600

ffmpeg -i $playlist_file -c copy -bsf:a aac_adtstoasc -f segment -segment_time $segment_duration an-$(date +"%d-%m-%Y")_%01d.mkv
