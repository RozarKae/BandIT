"""
BandIT - IELTS Writing Module Scaffolding & Evaluation Architecture.
Covers Task 1 (Academic Chart/Graph / General Letter) and Task 2 (Discursive Essay).
Rubric: Task Achievement/Response (TR), Coherence & Cohesion (CC), Lexical Resource (LR), Grammatical Range & Accuracy (GRA).
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
import math


@dataclass
class WritingTaskPrompt:
    id: str
    task_type: str  # "TASK_1_ACADEMIC", "TASK_1_GENERAL", "TASK_2_ESSAY"
    title: str
    prompt_text: str
    min_words: int
    recommended_minutes: int
    image_url: Optional[str] = None


@dataclass
class WritingTaskScore:
    task_id: str
    task_type: str
    overall_task_band: float
    task_response_band: float
    coherence_cohesion_band: float
    lexical_resource_band: float
    grammatical_range_band: float
    word_count: int
    is_underlength_penalty: bool
    feedback_summary: str
    detailed_critique: Dict[str, List[str]]
    sentence_corrections: List[Dict[str, str]]


class IELTSWritingEvaluator:
    """
    Evaluates IELTS Writing Task 1 and Task 2 submissions.
    """

    @staticmethod
    def calculate_writing_band(task1_band: float, task2_band: float) -> float:
        """
        IELTS Writing weighting: Task 2 is weighted twice as heavily as Task 1.
        Overall = (Task 1 + 2 * Task 2) / 3, rounded to nearest 0.5.
        """
        weighted_avg = (task1_band + (2.0 * task2_band)) / 3.0
        whole = math.floor(weighted_avg)
        fraction = weighted_avg - whole

        if fraction < 0.25:
            rounded_fraction = 0.0
        elif fraction < 0.75:
            rounded_fraction = 0.5
        else:
            rounded_fraction = 1.0

        return round(whole + rounded_fraction, 1)

    @staticmethod
    def analyze_word_count(essay_text: str, min_words: int = 250) -> Dict[str, Any]:
        """Verify word count and penalty thresholds."""
        words = re.findall(r"\b[A-Za-z'-]+\b", essay_text)
        count = len(words)
        return {
            "word_count": count,
            "min_words": min_words,
            "meets_requirement": count >= min_words,
            "deficit": max(0, min_words - count)
        }
