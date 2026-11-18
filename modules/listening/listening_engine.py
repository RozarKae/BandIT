"""
BandIT - IELTS Listening Module Scaffolding & Scoring Engine.
Handles audio playback timing, 4-part structure, spelling sensitivity,
and official 0-40 raw to band conversion.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ListeningQuestion:
    id: str
    section: int  # 1, 2, 3, or 4
    question_number: int
    prompt: str
    question_type: str  # "FORM_FILLING", "MULTIPLE_CHOICE", "MAP_LABELING", "MATCHING"
    correct_answers: List[str]  # e.g., ["9:30 am", "9.30", "09:30"]
    word_limit_instruction: str = "NO MORE THAN TWO WORDS AND/OR A NUMBER"


@dataclass
class ListeningSection:
    section_number: int
    context_type: str  # e.g., "Everyday Social Conversation", "Academic Lecture"
    audio_url: str
    transcript: str
    questions: List[ListeningQuestion]


class IELTSListeningScorer:
    """
    Official Cambridge IELTS Listening Raw to Band score mapping.
    """

    LISTENING_RAW_TO_BAND = [
        (39, 40, 9.0),
        (37, 38, 8.5),
        (35, 36, 8.0),
        (32, 34, 7.5),
        (30, 31, 7.0),
        (26, 29, 6.5),
        (23, 25, 6.0),
        (18, 22, 5.5),
        (16, 17, 5.0),
        (13, 15, 4.5),
        (10, 12, 4.0),
        (8, 9, 3.5),
        (6, 7, 3.0),
        (4, 5, 2.5),
        (0, 3, 2.0)
    ]

    @classmethod
    def calculate_band(cls, raw_correct_out_of_40: int) -> float:
        score = max(0, min(40, raw_correct_out_of_40))
        for low, high, band in cls.LISTENING_RAW_TO_BAND:
            if low <= score <= high:
                return band
        return 0.0

    @staticmethod
    def check_answer(user_answer: str, acceptable_answers: List[str]) -> bool:
        """Case-insensitive and whitespace-stripped answer comparison."""
        cleaned = user_answer.strip().lower()
        return any(cleaned == acc.strip().lower() for acc in acceptable_answers)
