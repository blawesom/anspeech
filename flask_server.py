from flask import Flask, request, jsonify
import subprocess
from threading import Thread
from datetime import datetime

app = Flask(__name__)

def process_stream(url, stream_number, segment_duration):
# Get current date and hour
  now = datetime.now()
  date_str = now.strftime("%d-%m-%Y")
  hour_str = now.strftime("%H%M")

  # Generate output filename prefix
  filename_prefix = f"an-{date_str}-{hour_str}-{stream_number}"

  # Construct ffmpeg command
  ffmpeg_cmd = f"ffmpeg -i {url} -c copy -bsf:a aac_adtstoasc -f segment -segment_time {segment_duration} ./output/{filename_prefix}_%02d.mkv"

  try:
    # Run ffmpeg command
    subprocess.run(ffmpeg_cmd.split(), check=True)
  except subprocess.CalledProcessError as e:
    print(f"FFmpeg error: {e}")  # Log the error for debugging


@app.route('/get_stream', methods=['POST'])
def get_strean():
  """
  Receives data containing playlist URL, stream number, and segment duration in JSON format and processes it using ffmpeg.
  """
  data = request.get_json()
  url = data.get('url')
  stream_number = url.split('/')[-1].split('.')[0]
  segment_duration = data.get('segment_duration', 300)  # Default 5 minutes

  if not url or not stream_number:
    return jsonify({'error': 'Missing required data (url or stream_number)'}), 400

  # Create and start a separate thread for ffmpeg processing
  thread = Thread(target=process_stream, args=(url, stream_number, segment_duration))
  thread.start()

  return jsonify({'message': 'Stream processing initiated'}), 202 


if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
