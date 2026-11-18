"""
IELTS Speaking Examiner State Machine.
Controls turn-taking, timing rules, cues, and dynamic follow-up triggers across Parts 1, 2, and 3.
"""

from typing import List, Optional, Dict, Any, Tuple
import datetime
import uuid

from examiner_engine.models import (
    ExamStage,
    Speaker,
    Part1Question,
    Part2CueCard,
    Part3Question,
    IELTSTestSet,
    TranscriptEntry,
    ExaminerAction
)
from examiner_engine.examiner_persona import (
    ExaminerPersonaHelper,
    OFFICIAL_SCRIPTS
)


class IELTSExaminerSession:
    """
    Manages an active IELTS Speaking interview session state.
    """

    def __init__(self, test_set: IELTSTestSet, candidate_name: str = "Candidate"):
        self.session_id: str = str(uuid.uuid4())
        self.test_set: IELTSTestSet = test_set
        self.candidate_name: str = candidate_name
        self.created_at: str = datetime.datetime.now().isoformat()
        
        # State tracking
        self.stage: ExamStage = ExamStage.IDLE
        self.transcript: List[TranscriptEntry] = []
        
        # Part 1 counters
        self.current_part1_idx: int = 0
        self.current_topic: Optional[str] = None
        
        # Part 2 state
        self.part2_prep_started_at: Optional[float] = None
        self.part2_has_spoken_sub_minute: bool = False
        self.part2_round_off_idx: int = 0
        
        # Part 3 counters
        self.current_part3_idx: int = 0
        self.part3_probed_for_current: bool = False

    def start_exam(self) -> ExaminerAction:
        """Start the IELTS interview with greeting and ID verification."""
        self.stage = ExamStage.PART1_ID_CHECK
        greeting = ExaminerPersonaHelper.get_greeting()
        
        self._record_utterance(Speaker.EXAMINER, greeting)
        return ExaminerAction(
            stage=self.stage,
            utterance=greeting,
            requires_candidate_input=True,
            input_timeout_seconds=30
        )

    def handle_candidate_response(
        self,
        candidate_text: str,
        duration_seconds: float = 20.0
    ) -> ExaminerAction:
        """
        Process candidate's spoken response and return the examiner's next action.
        """
        # Record candidate transcript entry
        self._record_utterance(
            Speaker.CANDIDATE,
            candidate_text,
            duration_seconds=duration_seconds
        )

        # Route response based on current stage
        if self.stage == ExamStage.PART1_ID_CHECK:
            return self._transition_to_part1_questions()

        elif self.stage == ExamStage.PART1_QUESTIONS:
            return self._handle_part1_answer(candidate_text, duration_seconds)

        elif self.stage == ExamStage.PART2_SPEAKING:
            return self._handle_part2_monologue(candidate_text, duration_seconds)

        elif self.stage == ExamStage.PART2_ROUND_OFF:
            return self._handle_part2_round_off(candidate_text, duration_seconds)

        elif self.stage == ExamStage.PART3_DISCUSSION:
            return self._handle_part3_answer(candidate_text, duration_seconds)

        else:
            return ExaminerAction(
                stage=self.stage,
                utterance=ExaminerPersonaHelper.get_exam_conclusion(),
                requires_candidate_input=False
            )

    # -------------------------------------------------------------
    # Part 1 Flow
    # -------------------------------------------------------------
    def _transition_to_part1_questions(self) -> ExaminerAction:
        self.stage = ExamStage.PART1_QUESTIONS
        self.current_part1_idx = 0
        first_q = self.test_set.part1_questions[0]
        self.current_topic = first_q.topic

        utterance = f"{ExaminerPersonaHelper.get_part1_intro()} Let's talk about {first_q.topic}. {first_q.question_text}"
        self._record_utterance(Speaker.EXAMINER, utterance, question_id=first_q.id)

        return ExaminerAction(
            stage=self.stage,
            utterance=utterance,
            requires_candidate_input=True,
            input_timeout_seconds=40
        )

    def _handle_part1_answer(self, candidate_text: str, duration_seconds: float) -> ExaminerAction:
        self.current_part1_idx += 1

        # Check if Part 1 questions are complete
        if self.current_part1_idx >= len(self.test_set.part1_questions):
            return self._transition_to_part2_cue_card()

        next_q = self.test_set.part1_questions[self.current_part1_idx]
        
        # Check if topic switched
        topic_intro = ""
        if next_q.topic != self.current_topic:
            self.current_topic = next_q.topic
            topic_intro = f"Thank you. Now let's talk about {next_q.topic}. "
        else:
            # Over-length polite interruption or standard acknowledgement
            eval_result = ExaminerPersonaHelper.evaluate_response_depth(candidate_text, duration_seconds)
            if eval_result == "TOO_LONG":
                topic_intro = "Thank you. Moving on, "
            else:
                topic_intro = "Thank you. "

        utterance = f"{topic_intro}{next_q.question_text}"
        self._record_utterance(Speaker.EXAMINER, utterance, question_id=next_q.id)

        return ExaminerAction(
            stage=self.stage,
            utterance=utterance,
            requires_candidate_input=True,
            input_timeout_seconds=40
        )

    # -------------------------------------------------------------
    # Part 2 Flow
    # -------------------------------------------------------------
    def _transition_to_part2_cue_card(self) -> ExaminerAction:
        self.stage = ExamStage.PART2_CUE_CARD_PRESENTED
        cue_card = self.test_set.part2_cue_card
        
        utterance = (
            f"{ExaminerPersonaHelper.get_part2_intro()}\n\n"
            f"Topic: {cue_card.title}\n"
            f"You should say:\n" + "\n".join(f"• {p}" for p in cue_card.prompts) + "\n\n"
            f"{ExaminerPersonaHelper.get_part2_prep_start()}"
        )
        self._record_utterance(Speaker.EXAMINER, utterance, question_id=cue_card.id)

        return ExaminerAction(
            stage=ExamStage.PART2_PREPARATION,
            utterance=utterance,
            requires_candidate_input=False,
            display_cue_card={
                "id": cue_card.id,
                "title": cue_card.title,
                "prompts": cue_card.prompts,
                "prep_time_seconds": cue_card.prep_time_seconds,
                "target_speaking_seconds": cue_card.target_speaking_seconds
            },
            timer_countdown_seconds=cue_card.prep_time_seconds
        )

    def trigger_part2_prep_finished(self) -> ExaminerAction:
        """Triggered automatically when the 60s prep timer finishes."""
        self.stage = ExamStage.PART2_SPEAKING
        cue_card = self.test_set.part2_cue_card
        utterance = ExaminerPersonaHelper.get_part2_prep_end()

        self._record_utterance(Speaker.EXAMINER, utterance, question_id=cue_card.id)

        return ExaminerAction(
            stage=self.stage,
            utterance=utterance,
            requires_candidate_input=True,
            input_timeout_seconds=cue_card.target_speaking_seconds,
            timer_countdown_seconds=cue_card.target_speaking_seconds
        )

    def _handle_part2_monologue(self, candidate_text: str, duration_seconds: float) -> ExaminerAction:
        cue_card = self.test_set.part2_cue_card

        # If candidate stopped speaking under 60 seconds and hasn't been prompted yet
        if duration_seconds < 60 and not self.part2_has_spoken_sub_minute:
            self.part2_has_spoken_sub_minute = True
            utterance = ExaminerPersonaHelper.get_part2_prep_start()
            prompt_more = "Can you tell me anything more about that?"
            self._record_utterance(Speaker.EXAMINER, prompt_more, question_id=cue_card.id)
            return ExaminerAction(
                stage=self.stage,
                utterance=prompt_more,
                requires_candidate_input=True,
                input_timeout_seconds=60,
                context_note="Candidate spoke for under 1 minute; prompt for elaboration."
            )

        # Transition to round-off questions
        self.stage = ExamStage.PART2_ROUND_OFF
        self.part2_round_off_idx = 0
        
        interruption_prefix = "Thank you. "
        if duration_seconds >= 120:
            interruption_prefix = "Thank you. I'm going to stop you there. "

        if cue_card.round_off_questions:
            first_roundoff = cue_card.round_off_questions[0]
            utterance = f"{interruption_prefix}{first_roundoff}"
            self._record_utterance(Speaker.EXAMINER, utterance)
            return ExaminerAction(
                stage=self.stage,
                utterance=utterance,
                requires_candidate_input=True,
                input_timeout_seconds=25
            )
        else:
            return self._transition_to_part3_discussion()

    def _handle_part2_round_off(self, candidate_text: str, duration_seconds: float) -> ExaminerAction:
        cue_card = self.test_set.part2_cue_card
        self.part2_round_off_idx += 1

        if self.part2_round_off_idx < len(cue_card.round_off_questions):
            next_roundoff = cue_card.round_off_questions[self.part2_round_off_idx]
            utterance = f"Thank you. {next_roundoff}"
            self._record_utterance(Speaker.EXAMINER, utterance)
            return ExaminerAction(
                stage=self.stage,
                utterance=utterance,
                requires_candidate_input=True,
                input_timeout_seconds=25
            )

        return self._transition_to_part3_discussion()

    # -------------------------------------------------------------
    # Part 3 Flow
    # -------------------------------------------------------------
    def _transition_to_part3_discussion(self) -> ExaminerAction:
        self.stage = ExamStage.PART3_DISCUSSION
        self.current_part3_idx = 0
        self.part3_probed_for_current = False

        first_p3 = self.test_set.part3_questions[0]
        intro = ExaminerPersonaHelper.get_part3_intro(self.test_set.part2_cue_card.topic)
        utterance = f"{intro} {first_p3.question_text}"

        self._record_utterance(Speaker.EXAMINER, utterance, question_id=first_p3.id)

        return ExaminerAction(
            stage=self.stage,
            utterance=utterance,
            requires_candidate_input=True,
            input_timeout_seconds=60
        )

    def _handle_part3_answer(self, candidate_text: str, duration_seconds: float) -> ExaminerAction:
        current_q = self.test_set.part3_questions[self.current_part3_idx]
        eval_result = ExaminerPersonaHelper.evaluate_response_depth(
            candidate_text, duration_seconds, is_part3=True
        )

        # Dynamic follow-up probe if response was too short and hasn't been probed yet
        if eval_result == "TOO_SHORT" and not self.part3_probed_for_current:
            self.part3_probed_for_current = True
            probe_question = ExaminerPersonaHelper.select_part3_probe(candidate_text, current_q.sub_probes)
            self._record_utterance(Speaker.EXAMINER, probe_question, question_id=current_q.id)
            return ExaminerAction(
                stage=self.stage,
                utterance=probe_question,
                requires_candidate_input=True,
                input_timeout_seconds=45,
                context_note="Adaptive probe triggered due to brief/superficial answer."
            )

        # Advance to next Part 3 question
        self.current_part3_idx += 1
        self.part3_probed_for_current = False

        if self.current_part3_idx >= len(self.test_set.part3_questions):
            return self._conclude_exam()

        next_q = self.test_set.part3_questions[self.current_part3_idx]
        prefix = "Thank you. "
        if eval_result == "TOO_LONG":
            prefix = "Thank you. Moving on to another aspect, "

        utterance = f"{prefix}{next_q.question_text}"
        self._record_utterance(Speaker.EXAMINER, utterance, question_id=next_q.id)

        return ExaminerAction(
            stage=self.stage,
            utterance=utterance,
            requires_candidate_input=True,
            input_timeout_seconds=60
        )

    # -------------------------------------------------------------
    # Completion & Export
    # -------------------------------------------------------------
    def _conclude_exam(self) -> ExaminerAction:
        self.stage = ExamStage.COMPLETED
        conclusion = ExaminerPersonaHelper.get_exam_conclusion()
        self._record_utterance(Speaker.EXAMINER, conclusion)

        return ExaminerAction(
            stage=self.stage,
            utterance=conclusion,
            requires_candidate_input=False
        )

    def _record_utterance(
        self,
        speaker: Speaker,
        text: str,
        duration_seconds: Optional[float] = None,
        question_id: Optional[str] = None
    ) -> TranscriptEntry:
        entry = TranscriptEntry(
            speaker=speaker,
            stage=self.stage,
            text=text,
            duration_seconds=duration_seconds,
            question_id=question_id
        )
        self.transcript.append(entry)
        return entry

    def export_session_payload(self) -> Dict[str, Any]:
        """
        Export the complete session transcript and metadata for the Scoring Engine.
        """
        return {
            "session_id": self.session_id,
            "candidate_name": self.candidate_name,
            "test_set_id": self.test_set.id,
            "test_theme": self.test_set.topic_theme,
            "total_turns": len(self.transcript),
            "transcript": [
                {
                    "speaker": e.speaker.value,
                    "stage": e.stage.value,
                    "text": e.text,
                    "timestamp": e.timestamp,
                    "duration_seconds": e.duration_seconds,
                    "question_id": e.question_id
                }
                for e in self.transcript
            ]
        }
