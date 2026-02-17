#!/usr/bin/env python3
"""
Transcription module using WhisperX with optional pyannote speaker diarization.

Replaces the direct `whisper` CLI call from antranscript.sh with a Python-based
pipeline that supports speaker diarization via pyannote.audio.

Usage:
    python transcribe.py <audio_file>

Outputs a .txt file next to the input audio file with speaker-attributed text
(when diarization is enabled) or plain text (when disabled).
"""

import sys
import os
import logging

import torch

# Monkey-patch torch.load to disable weights_only by default
# This fixes pickle.UnpicklingError with OmegaConf-based models in PyTorch 2.6+
# Security is not a concern for this project
_original_torch_load = torch.load

def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs or kwargs['weights_only'] is None:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

torch.load = _patched_torch_load

# Also patch PyTorch Lightning's _load function which is used by pyannote
from lightning_fabric.utilities.cloud_io import _load as pl_load_original
import lightning_fabric.utilities.cloud_io as cloud_io

def _patched_pl_load(path_or_url, map_location=None, weights_only=None):
    # Force weights_only=False for all loads
    return pl_load_original(path_or_url, map_location, weights_only=False)

cloud_io._load = _patched_pl_load

import whisperx
from whisperx.diarize import DiarizationPipeline

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DEVICE = "cuda"
COMPUTE_TYPE = "float32"


def load_diarization_pipeline():
    """Load pyannote diarization pipeline if enabled and token is available."""
    if not Config.DIARIZATION_ENABLED:
        log.info("Diarization is disabled via config.")
        return None

    if not Config.HF_TOKEN:
        log.warning(
            "DIARIZATION_ENABLED=true but HF_TOKEN is not set. "
            "Falling back to transcription without diarization."
        )
        return None

    log.info("Loading pyannote diarization pipeline...")
    try:
        pipeline = DiarizationPipeline(
            use_auth_token=Config.HF_TOKEN,
            device=DEVICE,
        )
        log.info("Diarization pipeline loaded.")
        return pipeline
    except AttributeError as e:
        log.error(
            "Failed to load diarization pipeline. This usually means:\n"
            "  1. You need to accept the user agreement for pyannote models at:\n"
            "     https://hf.co/pyannote/speaker-diarization-3.1\n"
            "     https://hf.co/pyannote/segmentation-3.0\n"
            "  2. Your HuggingFace token may not have the required permissions.\n"
            "  3. Run: huggingface-cli login --token %s\n"
            "Falling back to transcription without diarization.",
            Config.HF_TOKEN
        )
        return None


def transcribe_file(audio_path):
    """
    Transcribe an audio file with WhisperX, optionally adding speaker diarization.

    Returns the path to the output .txt file.
    """
    base, _ = os.path.splitext(audio_path)
    output_path = base + ".txt"

    log.info("Loading WhisperX model (model=%s, lang=%s)...", Config.WHISPER_MODEL, Config.WHISPER_LANGUAGE)
    model = whisperx.load_model(
        Config.WHISPER_MODEL,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        language=Config.WHISPER_LANGUAGE,
    )

    log.info("Loading audio: %s", audio_path)
    audio = whisperx.load_audio(audio_path)

    log.info("Running transcription...")
    result = model.transcribe(audio, batch_size=16, language=Config.WHISPER_LANGUAGE)
    log.info("Transcription complete (%d segments).", len(result["segments"]))

    # Word-level alignment (required for accurate diarization assignment)
    log.info("Aligning transcript for word-level timestamps...")
    align_model, metadata = whisperx.load_align_model(
        language_code=Config.WHISPER_LANGUAGE, device=DEVICE
    )
    result = whisperx.align(
        result["segments"], align_model, metadata, audio, device=DEVICE,
        return_char_alignments=False,
    )
    log.info("Alignment complete.")

    # Free alignment model memory
    del align_model

    # Diarization
    diarize_pipeline = load_diarization_pipeline()
    if diarize_pipeline is not None:
        log.info("Running speaker diarization...")
        diarize_kwargs = {}
        if Config.MIN_SPEAKERS:
            diarize_kwargs["min_speakers"] = Config.MIN_SPEAKERS
        if Config.MAX_SPEAKERS:
            diarize_kwargs["max_speakers"] = Config.MAX_SPEAKERS

        diarize_segments = diarize_pipeline(audio_path, **diarize_kwargs)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        log.info("Diarization complete.")

    # Format output
    lines = format_transcript(result["segments"], diarized=diarize_pipeline is not None)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    log.info("Transcript written to %s", output_path)
    return output_path


def format_transcript(segments, diarized=False):
    """
    Format segments into readable text lines.

    With diarization:
        [Speaker 1] Text of the segment...
        [Speaker 2] Text of the next segment...

    Without diarization:
        Text of the segment...
    """
    lines = []
    current_speaker = None

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        if diarized:
            speaker = seg.get("speaker", "Unknown")
            if speaker != current_speaker:
                current_speaker = speaker
                lines.append(f"\n[{speaker}]")
            lines.append(text)
        else:
            lines.append(text)

    return lines


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <audio_file>", file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]
    if not os.path.isfile(audio_path):
        log.error("File not found: %s", audio_path)
        sys.exit(1)

    transcribe_file(audio_path)


if __name__ == "__main__":
    main()
