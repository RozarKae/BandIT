"""
Audio Ingestion & High-Accuracy Speech Transcription Service.
Supports:
1. Google Gemini Native Multimodal Audio Transcription (verbatim disfluencies: "um", "uh", "er").
2. OpenAI Whisper-1 API (with verbatim disfluency prompt grounding).
3. Acoustic Feature Extraction (silence ratio, speech energy, pause intervals).
"""

import os
import base64
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple
from scoring_engine.audio_processor import AudioProcessor

# Try GenAI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


class AudioTranscriptionService:

    VERBATIM_TRANSCRIPTION_PROMPT = """
You are an IELTS Speech-to-Text Transcriber.
Transcribe the provided spoken audio VERBATIM.
CRITICAL TRANSCRIPTION RULES FOR IELTS SCORING:
1. Preserve every hesitation, repetition, false start, and filler sound: "um", "uh", "er", "ah", "like", "you know".
2. Do NOT correct the speaker's grammar, verb tenses, prepositions, or slip-ups.
3. Do NOT omit words or polish the speech.
4. Output JSON only in this format:
{
  "transcript": "...",
  "detected_fillers": ["um", "uh"],
  "estimated_tempo": "normal"
}
"""

    @classmethod
    def transcribe_audio_bytes(
        cls,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        client_hint_text: str = ""
    ) -> Dict[str, Any]:
        """
        Transcribe raw audio bytes using Gemini Audio or Whisper-1.
        Also runs acoustic feature extraction.
        """
        # 1. Run local acoustic extraction
        acoustic_metrics = AudioProcessor.analyze_raw_pcm(audio_bytes[:min(len(audio_bytes), 320000)])

        gemini_key = os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        # 2. Try Gemini Native Multimodal Audio
        if gemini_key:
            try:
                transcript_res = cls._transcribe_with_gemini(audio_bytes, mime_type, gemini_key)
                if transcript_res:
                    transcript_res["acoustic_features"] = acoustic_metrics
                    return transcript_res
            except Exception as e:
                print(f"Gemini audio transcription notice: {e}")

        # 3. Try OpenAI Whisper-1
        if openai_key:
            try:
                transcript_res = cls._transcribe_with_whisper(audio_bytes, mime_type, openai_key)
                if transcript_res:
                    transcript_res["acoustic_features"] = acoustic_metrics
                    return transcript_res
            except Exception as e:
                print(f"OpenAI Whisper audio transcription notice: {e}")

        # 4. Fallback if no cloud key configured
        fallback_text = client_hint_text or "Well, I use mobile applications constantly throughout the day for study and productivity."
        return {
            "transcript": fallback_text,
            "detected_fillers": ["um", "uh"] if "um" in fallback_text.lower() else [],
            "source": "client_speech_api_fallback",
            "acoustic_features": acoustic_metrics,
            "note": "Connect GEMINI_API_KEY or OPENAI_API_KEY in .env to enable direct cloud Whisper/Gemini transcription."
        }

    @classmethod
    def _transcribe_with_gemini(
        cls,
        audio_bytes: bytes,
        mime_type: str,
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini 2.5 Flash / 1.5 Pro native audio transcription."""
        if HAS_GENAI_SDK:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                        cls.VERBATIM_TRANSCRIPTION_PROMPT
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.0
                    )
                )
                if response and response.text:
                    parsed = json.loads(response.text)
                    parsed["source"] = "gemini_multimodal_audio"
                    return parsed
            except Exception as ex:
                print(f"GenAI SDK audio transcription failed: {ex}")

        # Direct REST API for Gemini Audio
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_audio
                            }
                        },
                        {"text": cls.VERBATIM_TRANSCRIPTION_PROMPT}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)
            parsed["source"] = "gemini_multimodal_audio_rest"
            return parsed

    @classmethod
    def _transcribe_with_whisper(
        cls,
        audio_bytes: bytes,
        mime_type: str,
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """Call OpenAI Whisper-1 transcription endpoint."""
        url = "https://api.openai.com/v1/audio/transcriptions"
        
        # Build multipart form data manually with boundary
        boundary = "----WebKitFormBoundaryIELTSWhisperAudio"
        ext = "webm" if "webm" in mime_type else "wav"
        
        parts = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-1\r\n".encode("utf-8"),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\num, uh, er, ah, like, you know, verbatim\r\n".encode("utf-8"),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"speech.{ext}\"\r\nContent-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            audio_bytes,
            f"\r\n--{boundary}--\r\n".encode("utf-8")
        ]
        
        body = b"".join(parts)
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            transcript = res_data.get("text", "")
            return {
                "transcript": transcript,
                "detected_fillers": [w for w in ["um", "uh", "er"] if w in transcript.lower()],
                "source": "openai_whisper_1"
            }
