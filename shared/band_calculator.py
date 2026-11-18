"""
BandIT - Shared IELTS Overall Band Calculator across all 4 modules:
1. Listening (L)
2. Reading (R)
3. Writing (W)
4. Speaking (S)
"""

import math
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import datetime


@dataclass
class BandITOverallProfile:
    candidate_name: str
    target_band: float
    listening_band: Optional[float] = None
    reading_band: Optional[float] = None
    writing_band: Optional[float] = None
    speaking_band: Optional[float] = None
    overall_band: float = 0.0
    cefr_level: str = "Unrated"
    evaluated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


class BandCalculator:
    """
    Computes official Cambridge IELTS Overall Band Score.
    """

    @staticmethod
    def calculate_overall(
        listening: float,
        reading: float,
        writing: float,
        speaking: float
    ) -> float:
        """
        Calculates overall band score:
        - If average ends in .25, rounds up to .5
        - If average ends in .75, rounds up to the next whole band
        - If fraction < .25, rounds down to .0
        - If fraction >= .25 and < .75, rounds to .5
        """
        scores = [listening, reading, writing, speaking]
        avg = sum(scores) / 4.0
        whole = math.floor(avg)
        fraction = avg - whole

        if fraction < 0.25:
            rounded_fraction = 0.0
        elif fraction < 0.75:
            rounded_fraction = 0.5
        else:
            rounded_fraction = 1.0

        return round(whole + rounded_fraction, 1)

    @staticmethod
    def get_cefr_level(band: float) -> str:
        """Maps IELTS band score to Common European Framework of Reference (CEFR)."""
        if band >= 8.5:
            return "C2 - Proficient / Mastery"
        elif band >= 7.0:
            return "C1 - Effective Operational Proficiency"
        elif band >= 5.5:
            return "B2 - Vantage / Independent User"
        elif band >= 4.0:
            return "B1 - Threshold / Intermediate"
        else:
            return "A2 - Waystage / Basic User"
