"""
Lightweight REST API Server for the IELTS Speaking Platform.
Connects the Frontend UI to the Examiner State Machine and Scoring Engine.
Zero external dependencies required (uses Python standard library http.server).
"""

import http.server
import socketserver
import json
import urllib.parse
from typing import Dict, Any
import sys
import os

# Add platform root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from examiner_engine.question_bank import ALL_TEST_SETS, get_test_set_by_id
from examiner_engine.state_machine import IELTSExaminerSession
from scoring_engine.scoring_pipeline import IELTSScoringPipeline
from scoring_engine.report_generator import ReportGenerator
from scoring_engine.audio_transcription_service import AudioTranscriptionService
from scoring_engine.llm_evaluator import MultiAgentLLMEvaluator
import base64

# In-memory session store
ACTIVE_SESSIONS: Dict[str, IELTSExaminerSession] = {}


class IELTSApiHandler(http.server.BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def _send_json_response(self, status_code: int, data: Any):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._send_json_response(200, {"status": "ok", "service": "IELTS Examiner & Scoring API"})

        elif path == "/api/topics":
            topics_data = []
            for ts in ALL_TEST_SETS:
                topics_data.append({
                    "id": ts.id,
                    "theme": ts.topic_theme,
                    "part1_topics": ts.part1_topics,
                    "part1_question_count": len(ts.part1_questions),
                    "part2_cue_card_title": ts.part2_cue_card.title,
                    "part3_question_count": len(ts.part3_questions)
                })
            self._send_json_response(200, {"topics": topics_data})

        elif path == "/api/settings":
            gemini_key = os.environ.get("GEMINI_API_KEY", "")
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            self._send_json_response(200, {
                "gemini_configured": bool(gemini_key),
                "gemini_masked_key": f"{gemini_key[:6]}...{gemini_key[-4:]}" if len(gemini_key) > 10 else "",
                "gemini_model": os.environ.get("GEMINI_MODEL", "gemini-1.5-pro"),
                "openai_configured": bool(openai_key),
                "openai_masked_key": f"{openai_key[:6]}...{openai_key[-4:]}" if len(openai_key) > 10 else "",
                "openai_model": os.environ.get("OPENAI_MODEL", "gpt-4o")
            })

        else:
            self._send_json_response(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

        # 0. Transcribe recorded audio
        if path == "/api/audio/transcribe":
            audio_b64 = body.get("audio_base64", "")
            mime_type = body.get("mime_type", "audio/webm")
            client_hint = body.get("client_hint", "")

            if audio_b64:
                # Remove data URL header if present (e.g. data:audio/webm;base64,...)
                if "," in audio_b64:
                    audio_b64 = audio_b64.split(",", 1)[1]
                audio_bytes = base64.b64decode(audio_b64)
            else:
                audio_bytes = b""

            res = AudioTranscriptionService.transcribe_audio_bytes(
                audio_bytes,
                mime_type=mime_type,
                client_hint_text=client_hint
            )
            self._send_json_response(200, res)

        # Settings: Test live connection
        elif path == "/api/settings/test":
            provider = body.get("provider", "gemini")
            api_key = body.get("api_key")
            model = body.get("model")
            res = MultiAgentLLMEvaluator.test_live_connection(provider, api_key, model)
            self._send_json_response(200, res)

        # Settings: Save key to environment & .env
        elif path == "/api/settings/save":
            provider = body.get("provider", "gemini")
            api_key = body.get("api_key", "").strip()
            model = body.get("model")
            if api_key:
                MultiAgentLLMEvaluator.save_api_key_to_env(provider, api_key, model)
            self._send_json_response(200, {"status": "ok", "provider": provider, "model": model})

        # 1. Start a new exam session
        elif path == "/api/sessions/start":
            test_set_id = body.get("test_set_id", "ielts_set_tech_01")
            candidate_name = body.get("candidate_name", "Candidate")

            test_set = get_test_set_by_id(test_set_id) or ALL_TEST_SETS[0]
            session = IELTSExaminerSession(test_set=test_set, candidate_name=candidate_name)
            ACTIVE_SESSIONS[session.session_id] = session

            action = session.start_exam()

            self._send_json_response(200, {
                "session_id": session.session_id,
                "candidate_name": candidate_name,
                "test_theme": test_set.topic_theme,
                "action": {
                    "stage": action.stage.value,
                    "utterance": action.utterance,
                    "requires_candidate_input": action.requires_candidate_input,
                    "input_timeout_seconds": action.input_timeout_seconds
                }
            })

        # 2. Progress candidate response or prep timer
        elif path == "/api/sessions/next":
            session_id = body.get("session_id")
            session = ACTIVE_SESSIONS.get(session_id)

            if not session:
                self._send_json_response(404, {"error": f"Session '{session_id}' not found."})
                return

            if body.get("is_prep_finished"):
                action = session.trigger_part2_prep_finished()
            else:
                candidate_text = body.get("candidate_text", "")
                duration_seconds = float(body.get("duration_seconds", 20.0))
                action = session.handle_candidate_response(candidate_text, duration_seconds)

            self._send_json_response(200, {
                "session_id": session.session_id,
                "action": {
                    "stage": action.stage.value,
                    "utterance": action.utterance,
                    "requires_candidate_input": action.requires_candidate_input,
                    "input_timeout_seconds": action.input_timeout_seconds,
                    "display_cue_card": action.display_cue_card,
                    "timer_countdown_seconds": action.timer_countdown_seconds,
                    "context_note": action.context_note
                }
            })

        # 3. Score the session
        elif path == "/api/sessions/score":
            session_id = body.get("session_id")
            session = ACTIVE_SESSIONS.get(session_id)

            if not session:
                # If session_id not in memory, check if full payload was passed directly
                if "transcript" in body:
                    payload = body
                else:
                    self._send_json_response(404, {"error": "Session not found and no transcript payload provided."})
                    return
            else:
                payload = session.export_session_payload()

            try:
                scorecard = IELTSScoringPipeline.evaluate_session(payload)
                scorecard_dict = ReportGenerator.to_dict(scorecard)
                markdown_report = ReportGenerator.to_markdown(scorecard)

                self._send_json_response(200, {
                    "scorecard": scorecard_dict,
                    "markdown_report": markdown_report
                })
            except ValueError as ve:
                self._send_json_response(400, {"error": str(ve)})
            except Exception as e:
                self._send_json_response(500, {"error": f"Scoring evaluation error: {str(e)}"})

        else:
            self._send_json_response(404, {"error": "Endpoint not found"})


def run_server(port: int = 8000):
    server_address = ("", port)
    with socketserver.TCPServer(server_address, IELTSApiHandler) as httpd:
        print(f"IELTS API Server running at http://127.0.0.1:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
