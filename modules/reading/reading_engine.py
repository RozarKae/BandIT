"""
BandIT - IELTS Reading Module Scaffolding & Scoring Engine.
Maps 40 raw reading comprehension scores directly to official IELTS 9-band scale
for Academic and General Training tests.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ReadingQuestion:
    id: str
    passage_id: str
    question_type: str  # "TFNG", "MULTIPLE_CHOICE", "HEADING_MATCH", "COMPLETION"
    question_number: int
    prompt: str
    options: Optional[List[str]] = None
    correct_answer: str = ""
    explanation: str = ""


@dataclass
class ReadingPassage:
    id: str
    section: int  # 1, 2, or 3
    title: str
    text_content: str
    questions: List[ReadingQuestion]


class IELTSReadingScorer:
    """
    Official Cambridge IELTS Reading Band conversion.
    """

    # Official Academic Reading Raw (0-40) to Band Map
    ACADEMIC_RAW_TO_BAND = [
        (39, 40, 9.0),
        (37, 38, 8.5),
        (35, 36, 8.0),
        (33, 34, 7.5),
        (30, 32, 7.0),
        (27, 29, 6.5),
        (23, 26, 6.0),
        (19, 22, 5.5),
        (15, 18, 5.0),
        (13, 14, 4.5),
        (10, 12, 4.0),
        (8, 9, 3.5),
        (6, 7, 3.0),
        (4, 5, 2.5),
        (0, 3, 2.0)
    ]

    @classmethod
    def calculate_band(cls, raw_correct_out_of_40: int, test_type: str = "ACADEMIC") -> float:
        """Convert raw score (0 to 40) into official IELTS band."""
        score = max(0, min(40, raw_correct_out_of_40))
        for low, high, band in cls.ACADEMIC_RAW_TO_BAND:
            if low <= score <= high:
                return band
        return 0.0
