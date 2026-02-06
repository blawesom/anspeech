from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psutil
import subprocess
from threading import Thread
from datetime import datetime
import os
from config import Config
from jobs import JobTracker

app = Flask(__name__, static_folder='web')
CORS(app)

job_tracker = JobTracker()

def process_stream(job_id, url, stream_number, segment_duration):
    try:
        now = datetime.now()
        date_str = now.strftime("%d-%m-%Y")
        hour_str = now.strftime("%H%M")
        filename_prefix = f"an-{date_str}-{hour_str}-{stream_number}"

        ffmpeg_cmd = f"ffmpeg -i {url} -c copy -bsf:a aac_adtstoasc -f segment -segment_time {segment_duration} {Config.OUTPUT_DIR}/{filename_prefix}_%02d.mkv"

        subprocess.run(ffmpeg_cmd.split(), check=True)
        job_tracker.update_job(job_id, 'completed')
    except subprocess.CalledProcessError as e:
        job_tracker.update_job(job_id, 'failed', error=str(e))


@app.route('/get_stream', methods=['POST'])
def get_stream():
    """
    Receives data containing playlist URL, stream number, and segment duration in JSON format and processes it using ffmpeg.
    """
    data = request.get_json()
    url = data.get('url')
    stream_number = url.split('/')[-1].split('.')[0]
    segment_duration = data.get('segment_duration', Config.SEGMENT_DURATION)

    if not url:
        return jsonify({'error': 'Missing required data (url)'}), 400

    active_jobs = job_tracker.get_active_jobs()
    if len(active_jobs) >= Config.MAX_CONCURRENT_STREAMS:
        return jsonify({'error': 'Maximum concurrent streams reached'}), 429

    if any(p.name() == "ffmpeg" for p in psutil.process_iter()):
        return jsonify({'error': 'Already processing a stream'}), 400

    job = job_tracker.add_job(url, segment_duration)
    thread = Thread(target=process_stream, args=(job['id'], url, stream_number, segment_duration))
    thread.start()

    return jsonify({'message': 'Stream processing initiated', 'job_id': job['id']}), 202


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List recent jobs with status"""
    jobs = job_tracker.get_recent_jobs()
    return jsonify(jobs)


@app.route('/api/transcripts', methods=['GET'])
def list_transcripts():
    """List available transcript files from S3 bucket"""
    transcripts = []

    try:
        # Use s3cmd to list files in the bucket
        result = subprocess.run(
            ['s3cmd', 'ls', Config.S3_BUCKET],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse s3cmd output
        # Format: "2024-01-23 12:34  123456  s3://public/23-01-2024.txt"
        for line in result.stdout.strip().split('\n'):
            if not line or not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 4:
                # Extract date, time, size and filename
                creation_date = parts[0]  # 2024-01-23
                creation_time = parts[1]  # 12:34
                size_bytes = int(parts[2])
                s3_path = parts[3]
                filename = s3_path.split('/')[-1]

                # Only include .txt files
                if filename.endswith('.txt'):
                    date = filename.replace('.txt', '')
                    # Combine date and time for sorting
                    creation_datetime = f"{creation_date} {creation_time}"
                    transcripts.append({
                        'date': date,
                        'filename': filename,
                        'url': f"{Config.S3_PUBLIC_URL}{filename}",
                        'size': f"{size_bytes / 1024:.1f} KB",
                        'created': creation_datetime
                    })

        # Sort by creation datetime in reverse order (newest first)
        transcripts.sort(key=lambda x: x['created'], reverse=True)

    except subprocess.CalledProcessError as e:
        # If s3cmd fails, return empty list
        print(f"S3 listing error: {e}")
    except Exception as e:
        print(f"Error parsing S3 output: {e}")

    return jsonify(transcripts)


@app.route('/api/transcripts/<filename>/content', methods=['GET'])
def get_transcript_content(filename):
    """Fetch transcript content from S3 and serve with proper encoding"""
    # Validate filename (only allow .txt files with date format)
    if not filename.endswith('.txt'):
        return jsonify({'error': 'Invalid file type'}), 400

    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        return jsonify({'error': 'Invalid filename'}), 400

    try:
        # Fetch file from S3 using s3cmd
        result = subprocess.run(
            ['s3cmd', 'get', f'{Config.S3_BUCKET}{safe_filename}', '--force', '-'],
            capture_output=True,
            check=True
        )

        # Return raw bytes directly to avoid Content-Length mismatch
        # When using strings, Flask calculates Content-Length from character count,
        # but UTF-8 multi-byte characters (é, è, à, ç) cause byte length to differ
        response = app.response_class(
            response=result.stdout,
            status=200,
            mimetype='text/plain; charset=utf-8'
        )
        return response

    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Transcript not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    ffmpeg_running = any(p.name() == "ffmpeg" for p in psutil.process_iter())
    return jsonify({
        'status': 'healthy',
        'ffmpeg_active': ffmpeg_running,
        'active_jobs': len(job_tracker.get_active_jobs()),
        'diarization_enabled': Config.DIARIZATION_ENABLED,
    })


@app.route('/')
def index():
    """Serve main page"""
    return send_from_directory('web', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('web', path)


if __name__ == '__main__':
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=8000, debug=False)
