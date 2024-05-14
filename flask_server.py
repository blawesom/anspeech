import flask
import subprocess
import os
import datetime
import json
import threading

app = flask.Flask(__name__)
lock_file = "lock.txt"

def check_url_processed(url):
    try:
        with open(lock_file, 'r') as file:
            if url in json.load(file):
                return True
    except FileNotFoundError:
        pass
    return False

def process_url(url):
    segment_time = "0:10"
    # Create the base FFmpeg command
    base_command = ["ffmpeg", "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", "-f", "segment"]

    # Split the segment time into hours and minutes
    hours, minutes = map(int, segment_time.split(":"))
    total_seconds = hours * 60 * 60 + minutes * 60

    # Iterate through each segment
    for i in range(0, total_seconds, segment_time):
        # Calculate the start time for this segment
        start_time = (i / 60) % 60
        end_time = (i / 60 + int(minutes/60) + 1) % 60

        # Construct the segment filename
        filename = f"an-{os.path.basename(url)}_{str(i // 60).zfill(2)}-{str(start_time).zfill(2)}.mkv"

        # Construct the segment command
        segment_command = base_command + ["-segment_time", f"{int(i)}", "-segment_atclocktime", f"{int(i)}:{str(start_time).zfill(2)}", filename]

        # Run the segment command
        subprocess.run(segment_command, check=True)

@app.route('/convert', methods=['POST'])
def convert():
    url = flask.request.json['url']

    if check_url_processed(url):
        return flask.jsonify({"message": "The URL is already being processed!"})

    process_thread = threading.Thread(target=process_url, args=(url))
    process_thread.start()
    today = datetime.now().strftime('%d-%m-%Y')
    return flask.jsonify({"message": f"Stream is being converted! You will find the result here: https://oos.eu-west-2.outscale.com/public/${today}.txt"})

if __name__ == '__main__':
    app.run(debug=True)
