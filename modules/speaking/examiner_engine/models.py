"""
Data models for the IELTS Speaking Question Bank, Examiner Persona, and State Machine.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import datetime
import uuid


class ExamStage(str, Enum):
    IDLE = "IDLE"
    PART1_ID_CHECK = "PART1_ID_CHECK"
    PART1_QUESTIONS = "PART1_QUESTIONS"
    PART2_CUE_CARD_PRESENTED = "PART2_CUE_CARD_PRESENTED"
    PART2_PREPARATION = "PART2_PREPARATION"
    PART2_SPEAKING = "PART2_SPEAKING"
    PART2_ROUND_OFF = "PART2_ROUND_OFF"
    PART3_DISCUSSION = "PART3_DISCUSSION"
    COMPLETED = "COMPLETED"


class Speaker(str, Enum):
    EXAMINER = "EXAMINER"
    CANDIDATE = "CANDIDATE"
    SYSTEM = "SYSTEM"


@dataclass
class Part1Question:
    id: str
    topic: str
    question_text: str
    target_duration_seconds: int = 25  # Ideal answer 20-30s
    key_themes: List[str] = field(default_factory=list)


@dataclass
class Part2CueCard:
    id: str
    topic: str
    title: str
    prompts: List[str]  # e.g., ["Where it was", "When you went there", "What you did", "And explain why..."]
    round_off_questions: List[str]  # 1-2 brief closing questions
    prep_time_seconds: int = 60
    target_speaking_seconds: int = 120  # 1 to 2 minutes


@dataclass
class Part3Question:
    id: str
    theme: str
    question_text: str
    target_duration_seconds: int = 45  # Ideal answer 35-50s
    sub_probes: List[str] = field(default_factory=list)  # Adaptive follow-ups


@dataclass
class IELTSTestSet:
    id: str
    topic_theme: str
    part1_topics: List[str]  # E.g. ["Hometown", "Reading"]
    part1_questions: List[Part1Question]
    part2_cue_card: Part2CueCard
    part3_questions: List[Part3Question]


@dataclass
class TranscriptEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    speaker: Speaker = Speaker.EXAMINER
    stage: ExamStage = ExamStage.IDLE
    text: str = ""
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    duration_seconds: Optional[float] = None
    question_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExaminerAction:
    stage: ExamStage
    utterance: str
    requires_candidate_input: bool = True
    input_timeout_seconds: Optional[int] = None
    display_cue_card: Optional[Dict[str, Any]] = None
    timer_countdown_seconds: Optional[int] = None
    is_interruption: bool = False
    context_note: Optional[str] = None
