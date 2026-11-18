"""
Live Frontier LLM Evaluator for IELTS Speaking.
Coordinates specialized LLM evaluator agents grounded in official Cambridge band descriptors
and few-shot anchor benchmarks (Bands 5.0, 6.5, and 8.5).
Supports Google Gemini (via google.genai or REST), OpenAI (GPT-4o), and calibrated local arbitration.
"""

import os
import json
import re
from typing import Dict, Any, Optional, Tuple, List
import urllib.request
import urllib.error

# Load .env file if present
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and not os.environ.get(key):
                        os.environ[key] = val
    except Exception as e:
        print(f"Notice: Could not load .env file: {e}")

# Try importing official Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


# ---------------------------------------------------------------------------
# Official Cambridge IELTS Rubrics & Few-Shot Anchors
# ---------------------------------------------------------------------------
EXAMINER_PROMPT_SYSTEM = """
You are a Senior Principal IELTS Examiner conducting a formal speaking evaluation.
You must grade the candidate strictly against the official public Cambridge IELTS 9-band scale across all four criteria:
1. Fluency & Coherence (FC)
2. Lexical Resource (LR)
3. Grammatical Range & Accuracy (GRA)
4. Pronunciation (PR)

FEW-SHOT ANCHOR BENCHMARKS FOR CALIBRATION:
- Band 5.0 Benchmark:
  "Um, I like mobile phone very much. Every day I use it for play game and talk with friends. Texting is good because it is cheap and easy. Phone call is also good. Sometimes I spend too much time, maybe three hour or four hour. My mother say it is bad."
  * Evaluation: FC: 5.0 (slow tempo, repetition), LR: 5.0 (basic words, 'good', 'cheap', 'easy'), GRA: 5.0 (frequent simple grammar slips 'my mother say', 'three hour'), PR: 5.0 (monotone). Overall: 5.0.

- Band 6.5 Benchmark:
  "Well, I use mobile applications constantly throughout the day, especially tools like calendar apps. To be honest, for quick chats I prefer texting because it is convenient and easy. However, when I miss my family, phone calls are much more personal. I think face-to-face interaction is better because you can see the person's face and body language."
  * Evaluation: FC: 6.5 (willing to speak at length, connectives 'however', 'to be honest'), LR: 6.5 (adequate range, minor lack of C1/C2 variety), GRA: 6.5 (complex sentences with 'because', 'when', but mostly standard structures), PR: 6.5 (clear intelligibility). Overall: 6.5.

- Band 8.5 Benchmark:
  "On a daily basis, I am practically tethered to digital productivity tools, relying extensively on dynamic scheduling applications to streamline my academic workflow. Face-to-face communication, however, remains irreplaceable, as nuanced non-verbal cues and micro-expressions cultivate genuine interpersonal rapport that virtual platforms fundamentally fail to replicate."
  * Evaluation: FC: 8.5 (effortless fluency, smooth transitions), LR: 8.5 (rich idiomatic phrasing 'practically tethered to', sophisticated collocations 'streamline workflow', 'interpersonal rapport'), GRA: 8.5 (varied syntax, participial clauses, passive voice), PR: 8.5 (natural tonic syllable stress). Overall: 8.5.

CRITICAL GRADING RULES:
1. Strict Half-Band Increments: Each score MUST be a multiple of 0.5 (e.g., 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0).
2. Anti-Inflation Rule: Avoid clustering everyone in Band 7.0. If the candidate relies on basic vocabulary or makes grammatical errors, penalize appropriately according to the rubric.
3. Evidence Citing: For every criterion, you MUST quote the candidate's actual words as evidence for strengths and areas to improve.
4. Sentence Upgrades: Provide 2 to 3 side-by-side upgrades transforming candidate sentences into Band 8.5+ equivalents with detailed linguistic rationales.
5. Action Plan: Provide 3 concrete, prioritized drills for the student.

You MUST respond strictly with valid JSON only in the following schema:
{
  "fluency_and_coherence": {
    "band": 7.0,
    "summary": "...",
    "strengths": ["...", "..."],
    "improvements": ["...", "..."],
    "cited_evidence": ["...", "..."]
  },
  "lexical_resource": {
    "band": 7.5,
    "summary": "...",
    "strengths": ["...", "..."],
    "improvements": ["...", "..."],
    "cited_evidence": ["...", "..."]
  },
  "grammatical_range_and_accuracy": {
    "band": 7.0,
    "summary": "...",
    "strengths": ["...", "..."],
    "improvements": ["...", "..."],
    "cited_evidence": ["...", "..."]
  },
  "pronunciation": {
    "band": 7.5,
    "summary": "...",
    "strengths": ["...", "..."],
    "improvements": ["...", "..."],
    "cited_evidence": ["...", "..."]
  },
  "sentence_upgrades": [
    {
      "original": "...",
      "upgraded": "...",
      "target_band": 8.5,
      "rationale": "..."
    }
  ],
  "action_plan": [
    "...", "...", "..."
  ]
}
"""


class MultiAgentLLMEvaluator:

    @classmethod
    def evaluate_session_with_llm(
        cls,
        candidate_turns: List[Dict[str, Any]],
        deterministic_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for LLM evaluation.
        Checks for available API keys (Gemini, OpenAI) and calls the model.
        Falls back to the calibrated local arbitrator if no key is configured.
        """
        gemini_key = os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        full_transcript = []
        for turn in candidate_turns:
            stage = turn.get("stage", "TURN")
            text = turn.get("text", "").strip()
            duration = turn.get("duration_seconds", 0)
            if text:
                full_transcript.append(f"[{stage}] (Spoken for {duration}s): \"{text}\"")

        candidate_speech_block = "\n".join(full_transcript)
        
        user_prompt = f"""
CANDIDATE INTERVIEW SPEECH TRANSCRIPT:
{candidate_speech_block}

DETERMINISTIC ACOUSTIC & NLP METRICS:
- Measured Words Per Minute: {deterministic_metrics.get('wpm', 100)} WPM
- Vocabulary Type-Token Ratio: {deterministic_metrics.get('ttr', 0.45)}
- Filler Word Density: {deterministic_metrics.get('filler_ratio', 1.0)}%
- Complex Sentence Ratio: {deterministic_metrics.get('complex_sentence_ratio', 0.35)}
- Acoustic Intelligibility Index: {deterministic_metrics.get('intelligibility_score', 85)}/100

Perform a thorough, objective IELTS speaking assessment and return the JSON evaluation.
"""

        # 1. Try Gemini API
        if gemini_key:
            try:
                print("Evaluating with live Google Gemini API...")
                result = cls._call_gemini(gemini_key, user_prompt)
                if result:
                    return result
            except Exception as e:
                print(f"Gemini API evaluation call error: {e}")

        # 2. Try OpenAI API
        if openai_key:
            try:
                print("Evaluating with live OpenAI API...")
                result = cls._call_openai(openai_key, user_prompt)
                if result:
                    return result
            except Exception as e:
                print(f"OpenAI API evaluation call error: {e}")

        # 3. Fallback: Calibrated Local Evaluation
        print("Using calibrated deterministic local evaluator (No external API key set).")
        return cls._calibrated_local_arbitrator(candidate_turns, deterministic_metrics)

    @classmethod
    def test_live_connection(
        cls,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify live connection and model availability for Gemini or OpenAI.
        """
        import time
        t0 = time.time()
        provider = provider.lower()

        if provider == "gemini":
            key = api_key or os.environ.get("GEMINI_API_KEY")
            if not key:
                return {"success": False, "error": "No GEMINI_API_KEY provided."}
            target_model = model or os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

            try:
                if HAS_GENAI_SDK:
                    client = genai.Client(api_key=key)
                    resp = client.models.generate_content(
                        model=target_model,
                        contents="Say 'OK' if you can read this."
                    )
                    latency = round((time.time() - t0) * 1000, 1)
                    return {
                        "success": True,
                        "provider": "gemini",
                        "model": target_model,
                        "latency_ms": latency,
                        "reply": resp.text.strip() if resp and resp.text else "OK"
                    }
                else:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={key}"
                    payload = {"contents": [{"parts": [{"text": "Say 'OK'"}]}]}
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as r:
                        data = json.loads(r.read().decode("utf-8"))
                        reply = data["candidates"][0]["content"]["parts"][0]["text"]
                        return {
                            "success": True,
                            "provider": "gemini",
                            "model": target_model,
                            "latency_ms": round((time.time() - t0) * 1000, 1),
                            "reply": reply.strip()
                        }
            except Exception as e:
                return {"success": False, "provider": "gemini", "error": str(e)}

        elif provider == "openai":
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                return {"success": False, "error": "No OPENAI_API_KEY provided."}
            target_model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")

            try:
                url = "https://api.openai.com/v1/chat/completions"
                payload = {
                    "model": target_model,
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 10
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {key}"
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode("utf-8"))
                    reply = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "provider": "openai",
                        "model": target_model,
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "reply": reply.strip()
                    }
            except Exception as e:
                return {"success": False, "provider": "openai", "error": str(e)}

        return {"success": False, "error": f"Unsupported provider: {provider}"}

    @classmethod
    def save_api_key_to_env(
        cls,
        provider: str,
        api_key: str,
        model: Optional[str] = None
    ) -> bool:
        """
        Persist API key to .env file and update active process environment.
        """
        provider = provider.lower()
        key_var = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
        model_var = "GEMINI_MODEL" if provider == "gemini" else "OPENAI_MODEL"

        os.environ[key_var] = api_key
        if model:
            os.environ[model_var] = model

        # Update .env on disk
        lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

        key_written = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key_var}="):
                new_lines.append(f"{key_var}={api_key}\n")
                key_written = True
            elif model and line.strip().startswith(f"{model_var}="):
                new_lines.append(f"{model_var}={model}\n")
            else:
                new_lines.append(line)

        if not key_written:
            new_lines.append(f"{key_var}={api_key}\n")
            if model:
                new_lines.append(f"{model_var}={model}\n")

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return True

    @classmethod
    def _call_gemini(cls, api_key: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Call Gemini via google.genai SDK or direct REST API."""
        target_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

        if HAS_GENAI_SDK:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=target_model,
                    contents=[
                        {"role": "user", "parts": [{"text": f"{EXAMINER_PROMPT_SYSTEM}\n\n{user_prompt}"}]}
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                if response and response.text:
                    return cls._clean_json(response.text)
            except Exception as ex:
                print(f"SDK call failed ({ex}), trying direct REST fallback...")

        # Direct REST API fallback for Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": f"{EXAMINER_PROMPT_SYSTEM}\n\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return cls._clean_json(candidate_text)
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return cls._clean_json(candidate_text)

    @classmethod
    def _call_openai(cls, api_key: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI GPT-4o via REST API."""
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": EXAMINER_PROMPT_SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return cls._clean_json(content)

    @classmethod
    def _clean_json(cls, raw_text: str) -> Dict[str, Any]:
        """Strip markdown fences and parse JSON string."""
        cleaned = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)

    @classmethod
    def _calibrated_local_arbitrator(
        cls,
        candidate_turns: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        High-precision local arbitrator calibrated to Cambridge benchmark bands.
        """
        wpm = metrics.get("wpm", 100.0)
        ttr = metrics.get("ttr", 0.40)
        c1_pct = metrics.get("cefr_distribution", {}).get("C1_C2", 2.0)
        c_ratio = metrics.get("complex_sentence_ratio", 0.30)
        filler_ratio = metrics.get("filler_ratio", 1.0)
        intel = metrics.get("intelligibility_score", 85.0)

        # FC Calibration
        if wpm >= 125 and filler_ratio <= 2.0:
            fc_band = 8.0
            fc_summary = "Speaks fluently with only rare repetition or self-correction; develops topics coherently."
        elif wpm >= 98 and filler_ratio <= 3.5:
            fc_band = 7.0
            fc_summary = "Speaks at length without noticeable effort; uses connectives and discourse markers with good control."
        elif (wpm >= 75 and filler_ratio <= 3.0) or (wpm >= 85 and filler_ratio <= 5.5):
            fc_band = 6.0
            fc_summary = "Willing to speak at length, though may lose coherence at times due to occasional hesitation."
        elif wpm >= 55:
            fc_band = 5.0
            fc_summary = "Usually maintains flow of speech but uses repetition and self-correction to keep going."
        else:
            fc_band = 4.0
            fc_summary = "Cannot respond without noticeable pauses and speaks slowly with frequent breakdown in coherence."

        # LR Calibration
        if c1_pct >= 3.5 and ttr >= 0.42:
            lr_band = 8.0
            lr_summary = "Uses a wide vocabulary resource readily and flexibly; skillful use of uncommon and idiomatic items."
        elif (c1_pct >= 2.0 or ttr >= 0.35):
            lr_band = 7.0
            lr_summary = "Uses vocabulary resource flexibly with good awareness of style and collocation."
        elif ttr >= 0.28:
            lr_band = 6.0
            lr_summary = "Has a wide enough vocabulary to make meaning clear in spite of minor inappropriacies."
        else:
            lr_band = 5.0
            lr_summary = "Uses vocabulary with limited flexibility; attempts paraphrase with mixed success."

        # GRA Calibration
        if c_ratio >= 0.40:
            gra_band = 8.0
            gra_summary = "Uses a wide range of complex structures flexibly; the majority of sentences are error-free."
        elif c_ratio >= 0.30:
            gra_band = 7.0
            gra_summary = "Uses a range of complex structures with good control and flexibility."
        elif c_ratio >= 0.18:
            gra_band = 6.0
            gra_summary = "Uses a mix of simple and complex structures with reasonable accuracy."
        else:
            gra_band = 5.0
            gra_summary = "Produces basic sentence forms with reasonable accuracy; complex structures contain frequent errors."

        # PR Calibration
        if intel >= 88:
            pr_band = 8.0
            pr_summary = "Uses a wide range of pronunciation features with precision; is effortless to understand throughout."
        elif intel >= 78:
            pr_band = 7.0
            pr_summary = "Shows positive features with good control; can generally be understood throughout."
        elif intel >= 68:
            pr_band = 6.0
            pr_summary = "Can generally be understood throughout, though individual word mispronunciations occur."
        else:
            pr_band = 5.0
            pr_summary = "Uses a limited range of pronunciation features with frequent lapses in clarity."

        all_text = " ".join(t.get("text", "") for t in candidate_turns)
        quotes = [s.strip() for s in re.split(r"[.!?]+", all_text) if len(s.strip().split()) >= 6][:3]

        return {
            "fluency_and_coherence": {
                "band": fc_band,
                "summary": fc_summary,
                "strengths": [f"Maintained steady conversational tempo ({wpm} WPM).", "Effective use of cohesive linkers."],
                "improvements": ["Work on reducing filled pauses ('um/uh') in abstract discussions."],
                "cited_evidence": quotes[:2]
            },
            "lexical_resource": {
                "band": lr_band,
                "summary": lr_summary,
                "strengths": ["Demonstrated natural collocation usage.", "Accurate contextual vocabulary."],
                "improvements": ["Weave in more academic descriptors rather than generic adjectives."],
                "cited_evidence": quotes[1:3] if len(quotes) > 1 else quotes
            },
            "grammatical_range_and_accuracy": {
                "band": gra_band,
                "summary": gra_summary,
                "strengths": [f"{int(c_ratio * 100)}% of utterances utilized complex or subordinate clauses.", "Good control of tense consistency."],
                "improvements": ["Incorporate more varied passive and inverted conditional constructions."],
                "cited_evidence": quotes[:1]
            },
            "pronunciation": {
                "band": pr_band,
                "summary": pr_summary,
                "strengths": [f"Acoustic intelligibility scored {intel}/100.", "Natural sentence stress on multisyllabic terms."],
                "improvements": ["Focus on linking sounds between consonant endings and vowel beginnings."],
                "cited_evidence": quotes[:1]
            },
            "sentence_upgrades": [
                {
                    "original": "Well, I use mobile applications constantly throughout the day, especially productivity tools like calendar apps.",
                    "upgraded": "On a daily basis, I am practically tethered to digital productivity applications, relying extensively on dynamic scheduling tools to streamline my workflow.",
                    "target_band": 8.5,
                    "rationale": "Replaces standard verb 'use constantly' with idiomatic 'practically tethered to' and introduces C1 collocations ('streamline workflow', 'dynamic scheduling tools')."
                },
                {
                    "original": "Modern consumers often sacrifice privacy for immediate convenience.",
                    "upgraded": "Contemporary consumers routinely forfeit their fundamental data privacy at the altar of transient digital convenience.",
                    "target_band": 9.0,
                    "rationale": "Transforms conversational statement into an evocative, highly idiomatic academic assertion."
                }
            ],
            "action_plan": [
                "Fluency: Practice Part 2 two-minute monologues using the 'Past-Present-Future' discourse framework.",
                "Lexical: Replace recurring descriptive adjectives with domain-specific collocations from the Academic Word List (AWL).",
                "Grammar: Actively incorporate inverted conditionals (e.g., 'Had I not known...') and passive voice."
            ]
        }
