# AnSpeech

Automated live stream transcription service with speaker diarization. Captures audio/video streams, transcribes them using WhisperX, identifies speakers via pyannote.audio, and publishes daily transcripts to S3.

## What It Does

1. Accepts stream URLs via web interface or API
2. Segments streams into 10-minute chunks (MKV)
3. Extracts audio (M4A) and transcribes to French text (WhisperX)
4. Identifies speakers using pyannote diarization (optional)
5. Publishes daily speaker-attributed transcripts to public S3 bucket

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env - set HF_TOKEN for speaker diarization (see below)

# Start service
./main.sh
```

## Speaker Diarization Setup

Speaker diarization uses [pyannote.audio](https://github.com/pyannote/pyannote.audio) to identify *who spoke when*. Transcripts are formatted with speaker labels:

```
[SPEAKER_00]
Bonjour, bienvenue dans cette emission.

[SPEAKER_01]
Merci de m'avoir invite.
```

### Prerequisites

1. Create a [Hugging Face](https://huggingface.co) account
2. Accept the pyannote model license at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
3. Generate an access token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Set `HF_TOKEN` in your `.env` file

### Disabling Diarization

Set `DIARIZATION_ENABLED=false` in `.env` to get plain text output (no speaker labels), equivalent to the previous Whisper-only behavior.

## Web Interface

Access the unified web interface at `http://localhost:8000/` to:
- Submit new stream URLs
- Monitor active jobs in real-time
- Browse and download transcripts with color-coded speaker labels

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

Returns diarization status:
```json
{
  "status": "healthy",
  "ffmpeg_active": false,
  "active_jobs": 0,
  "diarization_enabled": true
}
```

## Components

- **[config.py](config.py)** - Centralized configuration management
- **[jobs.py](jobs.py)** - Job tracking and state management
- **[flask_server.py](flask_server.py)** - REST API server with CORS support, S3 integration
- **[transcribe.py](transcribe.py)** - WhisperX transcription with pyannote diarization
- **[antranscript.sh](antranscript.sh)** - Transcription worker process
- **[web/index.html](web/index.html)** - Unified web interface with speaker label rendering
- **[clean.sh](clean.sh)** - Cleanup script for processes and old files

## Configuration

Configuration is managed via environment variables (`.env` file):

```bash
OUTPUT_DIR=./output              # Output directory for segments
SEGMENT_DURATION=600            # Segment duration in seconds
WHISPER_MODEL=large-v3          # WhisperX model (large-v3 recommended)
WHISPER_LANGUAGE=fr             # Transcription language

# Diarization (speaker identification)
DIARIZATION_ENABLED=true        # Enable/disable speaker diarization
HF_TOKEN=                       # Hugging Face token (required for diarization)
MIN_SPEAKERS=1                  # Minimum expected speakers (default: 1)
MAX_SPEAKERS=10                 # Maximum expected speakers (default: 10)

# Storage
S3_BUCKET=s3://public/          # S3 bucket for uploads
S3_PUBLIC_URL=https://...       # Public S3 URL
RETENTION_DAYS=7                # Days to keep old files
MAX_CONCURRENT_STREAMS=1        # Max simultaneous streams
```

## Requirements

- Python 3.x with WhisperX, pyannote.audio, Flask, PyTorch
- FFmpeg
- s3cmd (configured)
- NVIDIA GPU required (CUDA)
- Hugging Face account and token (for diarization)

## Cleanup

```bash
# Stop all processes and clean old files
./clean.sh
```

The cleanup script will:
- Terminate all ffmpeg, gunicorn, and transcription processes
- Delete files older than RETENTION_DAYS (default: 7 days)

## Access Transcripts

- Web interface: `http://localhost:8000/`
- Direct S3 URL: `https://oos.eu-west-2.outscale.com/public/DD-MM-YYYY.txt`

## License

MIT License
