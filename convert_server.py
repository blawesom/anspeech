import os
import subprocess
from datetime import datetime
from s3transfer.manager import TransferManager
from s3transfer.storage import S3Storage

def convert_video_to_audio(file):
    output = file.rstrip('.mkv') + '.m4a'
    subprocess.run(["ffmpeg", "-i", file, "-map", "0:1", "-c", "copy", output])

def convert_to_text(file):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output = file.rstrip('.m4a') + '.txt'
    subprocess.run(["whisper", file, "--model", "large", "--language", "fr", "--output_format", "txt", ">", output])

def upload_to_s3(file):
    today = datetime.now().strftime('%d-%m-%Y')
    storage = S3Storage('s3://public/')
    manager = TransferManager()
    manager.upload_file(file, storage, f'{today}.txt')

while True:
    for file in os.listdir():
        if file.endswith('.mkv'):
            convert_video_to_audio(file)
            convert_to_text(file)
            upload_to_s3(file)
