# Transcription & Diarization Evaluation

## Current Setup

AnSpeech currently uses **OpenAI Whisper** (`openai-whisper==20231117`, model: `large`, language: `fr`) for transcription. The pipeline segments live streams into 10-minute MKV chunks via FFmpeg, extracts audio to M4A, then runs Whisper to produce plain text. There is **no speaker diarization** — output is continuous text without speaker labels or timestamps.

---

## Why Add Diarization?

For multi-speaker content (debates, interviews, panel discussions), plain transcription produces an undifferentiated wall of text. Speaker diarization identifies *who spoke when*, enabling:

- Speaker-attributed transcripts (e.g., `Speaker 1: ...`, `Speaker 2: ...`)
- Better readability and searchability
- Downstream analytics (speaking time per participant, turn-taking patterns)

---

## Evaluated Alternatives

### Option 1: WhisperX + Pyannote (Open-Source, Self-Hosted)

**What it is:** WhisperX extends Whisper with word-level timestamps (via wav2vec2 forced alignment) and speaker diarization (via pyannote.audio). It uses faster-whisper under the hood for ~4x speed improvement.

| Aspect | Details |
|---|---|
| **Transcription** | faster-whisper (Whisper large-v3), French supported |
| **Diarization** | pyannote.audio 3.1 (DER ~11-19% on standard benchmarks) |
| **French support** | Pyannote was developed by French researchers (CNRS/IRIT), tested on French datasets (ALLIES, REPERE) |
| **Cost** | Free (open-source). GPU compute cost only |
| **Integration effort** | Medium — replace Whisper CLI call with WhisperX Python API |
| **Infrastructure** | Runs on existing NVIDIA GPU setup (CUDA 12.1 already in requirements) |

**Pros:**
- No API costs or per-minute billing — ideal for continuous stream processing
- Pyannote has strong French-language heritage and community
- Keeps all processing local (no data leaving the server)
- Word-level timestamps included for free
- 4x faster than standard Whisper via faster-whisper backend

**Cons:**
- Requires Hugging Face token and accepting pyannote model license
- DER varies with audio quality and number of speakers
- Must manage model updates and compatibility yourself
- No built-in overlapping speech handling in basic pipeline

**Integration sketch:**
```python
import whisperx

model = whisperx.load_model("large-v3", device="cuda", language="fr")
audio = whisperx.load_audio("segment.m4a")
result = model.transcribe(audio)

# Align for word-level timestamps
align_model, metadata = whisperx.load_align_model(language_code="fr", device="cuda")
result = whisperx.align(result["segments"], align_model, metadata, audio, device="cuda")

# Diarize
diarize_model = whisperx.DiarizationPipeline(use_auth_token="HF_TOKEN", device="cuda")
diarize_segments = diarize_model(audio)
result = whisperx.assign_word_speakers(diarize_segments, result)
```

---

### Option 2: Deepgram Nova-3 (Cloud API)

| Aspect | Details |
|---|---|
| **Transcription** | Nova-3 model, 5.26% WER |
| **Diarization** | Built-in, enabled via `diarize=true` parameter |
| **French support** | Yes (multilingual tier, higher pricing) |
| **Cost** | ~$0.0065-0.0077/min base + ~$0.001-0.002/min for diarization |
| **Integration effort** | Low — REST API, SDKs available |
| **Infrastructure** | Cloud-hosted, no GPU needed |

**Pros:**
- Very low integration effort (single API call)
- Real-time streaming support
- Smart formatting, punctuation, filler word detection included

**Cons:**
- Per-minute billing adds up fast for continuous streams (~$4-5/hr with French + diarization)
- Audio data leaves your infrastructure
- Multilingual pricing is higher than English-only
- Vendor lock-in

**Cost estimate for continuous use:** At 24h/day streaming, ~$100-120/day or ~$3,000-3,600/month.

---

### Option 3: AssemblyAI (Cloud API)

| Aspect | Details |
|---|---|
| **Transcription** | Universal model or Slam-1 (higher accuracy) |
| **Diarization** | Built-in, supports up to 50 speakers, 85-95% accuracy on clear audio |
| **French support** | Yes (99 languages supported) |
| **Cost** | $0.15/hr base + $0.02/hr diarization = $0.17/hr minimum |
| **Integration effort** | Low — REST API, Python SDK |
| **Infrastructure** | Cloud-hosted |

**Pros:**
- Lowest cloud API pricing for the feature set
- Up to 50 speakers per recording
- Additional NLU features available (sentiment, summarization, entity detection)
- Good documentation and Python SDK

**Cons:**
- Audio data leaves your infrastructure
- Additional features cost extra ($0.02-0.08/hr each)
- No real-time streaming diarization (batch processing only)
- Vendor dependency

**Cost estimate for continuous use:** ~$0.17/hr = ~$4/day or ~$124/month.

---

### Option 4: Google Cloud Speech-to-Text (Chirp 3)

| Aspect | Details |
|---|---|
| **Transcription** | Chirp 3 model, 125+ languages |
| **Diarization** | Built-in with V2 API |
| **French support** | Yes, strong multilingual model |
| **Cost** | Variable, negotiable for volume |
| **Integration effort** | Medium — requires GCP setup, V2 API (US region only currently) |
| **Infrastructure** | Cloud-hosted |

**Pros:**
- Best multilingual coverage (125+ languages)
- Diarization included in transcription pricing
- Strong enterprise support and SLAs

**Cons:**
- GCP ecosystem lock-in
- Chirp 3 V2 API limited to US region
- Complex pricing structure
- Requires GCP account and IAM setup

---

### Option 5: NVIDIA NeMo (Open-Source, Self-Hosted)

| Aspect | Details |
|---|---|
| **Transcription** | NeMo ASR models (Conformer, FastConformer) |
| **Diarization** | NeMo MSDD (Multi-Scale Diarization Decoder) |
| **French support** | Limited — primarily English-focused models |
| **Cost** | Free (open-source). GPU compute cost only |
| **Integration effort** | High — complex setup, separate transcription and diarization pipelines |
| **Infrastructure** | Requires NVIDIA GPU (existing hardware works) |

**Pros:**
- Fastest inference on NVIDIA GPUs
- Enterprise-grade, production-proven
- No API costs

**Cons:**
- French language support is weaker than Pyannote/Whisper
- Significantly more complex to set up and maintain
- Steeper learning curve
- Models are large and require substantial VRAM

---

## Comparison Matrix

| Criteria | WhisperX + Pyannote | Deepgram | AssemblyAI | Google Chirp 3 | NVIDIA NeMo |
|---|---|---|---|---|---|
| **French quality** | Good (French heritage) | Good | Good | Very good | Limited |
| **Diarization accuracy** | DER 11-19% | Good (proprietary) | 85-95% (clear audio) | Good (proprietary) | Good (English) |
| **Monthly cost (24/7)** | GPU only (~$0) | ~$3,000-3,600 | ~$124 | Negotiable | GPU only (~$0) |
| **Integration effort** | Medium | Low | Low | Medium | High |
| **Data privacy** | Full (on-premise) | Cloud | Cloud | Cloud | Full (on-premise) |
| **Latency** | Low (local) | Low (streaming) | Higher (batch) | Medium | Low (local) |
| **Maintenance burden** | Medium | None | None | Low | High |

---

## Recommendation

**Primary recommendation: WhisperX + Pyannote (Option 1)**

Rationale:
1. **Cost**: AnSpeech processes continuous streams. Cloud API costs at $0.17-5/hr would be $124-3,600/month. Self-hosted has zero marginal cost since the NVIDIA GPU is already provisioned.
2. **French**: Pyannote was built by French researchers and has been validated on French corpora. This is the most battle-tested open-source diarization for French.
3. **Architecture fit**: The existing pipeline already uses Whisper on a local GPU. WhisperX is a drop-in upgrade that adds diarization while also making transcription ~4x faster via faster-whisper.
4. **Privacy**: Audio never leaves the server, which may matter for certain broadcast content.
5. **Minimal change**: The core pipeline (FFmpeg segmentation -> audio extraction -> transcription -> S3 upload) stays the same. Only the transcription step changes from a Whisper CLI call to a WhisperX Python call.

**Fallback recommendation: AssemblyAI (Option 3)**

If self-hosted complexity is undesirable, AssemblyAI offers the best price-to-feature ratio among cloud APIs at $0.17/hr with diarization, and has solid French support.

---

## Implementation Path for WhisperX + Pyannote

1. **Add dependencies**: `whisperx`, `pyannote.audio` to `requirements.txt`
2. **Obtain Hugging Face token**: Accept pyannote model license on HuggingFace
3. **Add config**: `HF_TOKEN` env variable, `DIARIZATION_ENABLED` flag
4. **Replace transcription step**: Convert `antranscript.sh` Whisper CLI call to a Python script using WhisperX API
5. **Update output format**: Change from plain `.txt` to speaker-attributed format (e.g., `[Speaker 1] text...`)
6. **Update web UI**: Display speaker labels in transcript viewer
7. **Test**: Validate on sample French multi-speaker audio

### Required New Dependencies

```
whisperx>=3.1.0
pyannote.audio>=3.1.0
faster-whisper>=1.0.0
```

### New Environment Variables

```
HF_TOKEN=                        # Hugging Face access token for pyannote models
DIARIZATION_ENABLED=true         # Enable/disable speaker diarization
MIN_SPEAKERS=                    # Optional: minimum expected speakers (improves accuracy)
MAX_SPEAKERS=                    # Optional: maximum expected speakers (improves accuracy)
```

---

## Sources

- [WhisperX GitHub](https://github.com/m-bain/whisperX)
- [Whisper and Pyannote: The Ultimate Solution for Speech Transcription](https://scalastic.io/en/whisper-pyannote-ultimate-speech-transcription/)
- [Benchmarking Diarization Models (arxiv)](https://arxiv.org/html/2509.26177v1)
- [Deepgram Speech-to-Text APIs 2026](https://deepgram.com/learn/best-speech-to-text-apis-2026)
- [AssemblyAI Top Speaker Diarization Libraries](https://www.assemblyai.com/blog/top-speaker-diarization-libraries-and-apis)
- [Deepgram Pricing 2026](https://brasstranscripts.com/blog/deepgram-pricing-per-minute-2025-real-time-vs-batch)
- [AssemblyAI Pricing 2026](https://brasstranscripts.com/blog/assemblyai-pricing-per-minute-2025-real-costs)
- [AssemblyAI vs Deepgram Comparison](https://www.gladia.io/blog/assemblyai-vs-deepgram)
- [How to Evaluate Speaker Diarization Performance](https://www.pyannote.ai/blog/how-to-evaluate-speaker-diarization-performance)
