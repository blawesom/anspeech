import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # Paths
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')

    # Stream settings
    SEGMENT_DURATION = int(os.getenv('SEGMENT_DURATION', '600'))

    # Whisper settings
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large-v3')
    WHISPER_LANGUAGE = os.getenv('WHISPER_LANGUAGE', 'fr')

    # Diarization settings
    DIARIZATION_ENABLED = os.getenv('DIARIZATION_ENABLED', 'true').lower() == 'true'
    HF_TOKEN = os.getenv('HF_TOKEN', '')
    MIN_SPEAKERS = int(os.getenv('MIN_SPEAKERS', '1')) or None
    MAX_SPEAKERS = int(os.getenv('MAX_SPEAKERS', '10')) or None

    # S3 settings
    S3_BUCKET = os.getenv('S3_BUCKET', 's3://public/')
    S3_PUBLIC_URL = os.getenv('S3_PUBLIC_URL', 'https://oos.eu-west-2.outscale.com/public/')

    # Cleanup
    RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '7'))

    # API
    MAX_CONCURRENT_STREAMS = int(os.getenv('MAX_CONCURRENT_STREAMS', '1'))
