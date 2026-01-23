import os

class Config:
    # Paths
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')

    # Stream settings
    SEGMENT_DURATION = int(os.getenv('SEGMENT_DURATION', '600'))

    # Whisper settings
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large')
    WHISPER_LANGUAGE = os.getenv('WHISPER_LANGUAGE', 'fr')

    # S3 settings
    S3_BUCKET = os.getenv('S3_BUCKET', 's3://public/')
    S3_PUBLIC_URL = os.getenv('S3_PUBLIC_URL', 'https://oos.eu-west-2.outscale.com/public/')

    # Cleanup
    RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '7'))

    # API
    MAX_CONCURRENT_STREAMS = int(os.getenv('MAX_CONCURRENT_STREAMS', '1'))
