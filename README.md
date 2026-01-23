# AnSpeech

Automated live stream transcription service that captures audio/video streams, transcribes them using OpenAI Whisper, and publishes daily transcripts to S3.

## What It Does

1. Accepts stream URLs via web interface or API
2. Segments streams into 10-minute chunks (MKV)
3. Extracts audio (M4A) and transcribes to French text (Whisper)
4. Publishes daily transcripts to public S3 bucket

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env with your settings

# Start service
./main.sh
```

## Web Interface

Access the unified web interface at `http://localhost:8000/` to:
- Submit new stream URLs
- Monitor active jobs in real-time
- Browse and download transcripts

## API Endpoints

### Submit Stream
```bash
curl -X POST http://localhost:8000/get_stream \
  -H "Content-Type: application/json" \
  -d '{"url": "http://example.com/stream.m3u8", "segment_duration": 600}'
```

### List Jobs
```bash
curl http://localhost:8000/api/jobs
```

### List Transcripts
```bash
curl http://localhost:8000/api/transcripts
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

## Components

- **[config.py](config.py)** - Centralized configuration management
- **[jobs.py](jobs.py)** - Job tracking and state management
- **[flask_server.py](flask_server.py)** - REST API server with CORS support, S3 integration
- **[antranscript.sh](antranscript.sh)** - Transcription worker process
- **[web/index.html](web/index.html)** - Unified web interface
- **[clean.sh](clean.sh)** - Cleanup script for processes and old files
- **[deploy.sh](deploy.sh)** - Deployment automation

## Configuration

Configuration is managed via environment variables (`.env` file):

```bash
OUTPUT_DIR=./output              # Output directory for segments
SEGMENT_DURATION=600            # Segment duration in seconds
WHISPER_MODEL=large             # Whisper model size
WHISPER_LANGUAGE=fr             # Transcription language
S3_BUCKET=s3://public/          # S3 bucket for uploads
S3_PUBLIC_URL=https://...       # Public S3 URL
RETENTION_DAYS=7                # Days to keep old files
MAX_CONCURRENT_STREAMS=1        # Max simultaneous streams
```

## Requirements

- Python 3.x with Whisper, Flask, PyTorch
- FFmpeg
- s3cmd (configured)
- NVIDIA GPU recommended

## Cleanup

```bash
# Stop all processes and clean old files
./clean.sh
```

The cleanup script will:
- Terminate all ffmpeg, gunicorn, and transcription processes
- Delete files older than RETENTION_DAYS (default: 7 days)

## Deployment

```bash
# Automated deployment
./deploy.sh
```

## Access Transcripts

- Web interface: `http://localhost:8000/`
- Direct S3 URL: `https://oos.eu-west-2.outscale.com/public/DD-MM-YYYY.txt`

## License

MIT License
