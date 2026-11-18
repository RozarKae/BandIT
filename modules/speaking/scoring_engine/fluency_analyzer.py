"""
Fluency and Coherence (FC) Analyzer.
Extracts speech rate, pause estimates, filler word ratios, and discourse marker usage.
"""

import re
from typing import List, Dict, Any, Tuple
from scoring_engine.models import FluencyMetrics, CriterionScore

FILLER_PATTERNS = [
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\bah+\b",
    r"\blike\b(?=\s+[a-z]+)",
    r"\byou know\b",
    r"\bi mean\b",
    r"\bsort of\b",
    r"\bkind of\b"
]

DISCOURSE_MARKERS = [
    "furthermore", "moreover", "in addition", "consequently", "as a result",
    "on the other hand", "nevertheless", "however", "conversely", "in contrast",
    "for instance", "for example", "to illustrate", "to be honest", "without doubt",
    "undoubtedly", "therefore", "similarly", "first and foremost", "ultimately",
    "in particular", "broadly speaking", "from my perspective", "as far as i'm concerned"
]


class FluencyAnalyzer:

    @staticmethod
    def analyze(candidate_turns: List[Dict[str, Any]]) -> Tuple[FluencyMetrics, CriterionScore]:
        """
        Analyze candidate turns for speech rate, fillers, and coherence markers.
        """
        all_text = " ".join(t.get("text", "") for t in candidate_turns)
        total_duration = sum(t.get("duration_seconds") or 20.0 for t in candidate_turns)
        total_duration = max(total_duration, 1.0)

        # Tokenization
        words = re.findall(r"\b[A-Za-z'-]+\b", all_text.lower())
        total_words = len(words)

        # WPM Calculation
        minutes = total_duration / 60.0
        wpm = round(total_words / minutes, 1)

        # Filler words detection
        found_fillers = []
        for pat in FILLER_PATTERNS:
            matches = re.findall(pat, all_text, flags=re.IGNORECASE)
            found_fillers.extend(matches)
        
        filler_count = len(found_fillers)
        filler_freq_percent = round((filler_count / max(total_words, 1)) * 100, 2)

        # Discourse markers detection
        text_lower = all_text.lower()
        found_markers = [m for m in DISCOURSE_MARKERS if m in text_lower]

        # Estimated Pause Ratio: typical conversational speech is ~135 WPM without pauses.
        # Ratio reflects hesitation overhead.
        expected_time = total_words / (140.0 / 60.0)
        pause_overhead = max(0.0, total_duration - expected_time)
        pause_ratio = round(min(0.5, pause_overhead / total_duration), 2)

        metrics = FluencyMetrics(
            total_words=total_words,
            speaking_duration_seconds=round(total_duration, 1),
            words_per_minute=wpm,
            filler_word_count=filler_count,
            filler_words=found_fillers,
            filler_frequency_percent=filler_freq_percent,
            discourse_markers=found_markers,
            discourse_marker_count=len(found_markers),
            estimated_pause_ratio=pause_ratio
        )

        # Calibrate Fluency Band Score
        score = FluencyAnalyzer._calibrate_fc_band(metrics, all_text)
        return metrics, score

    @staticmethod
    def _calibrate_fc_band(metrics: FluencyMetrics, full_text: str) -> CriterionScore:
        wpm = metrics.words_per_minute
        filler_ratio = metrics.filler_frequency_percent
        markers_count = metrics.discourse_marker_count

        strengths = []
        improvements = []
        evidence = []

        # Heuristic Band Estimation according to IELTS Descriptors
        if wpm >= 125 and filler_ratio <= 2.0:
            band = 8.0
            summary = "Speaks fluently with only rare repetition or self-correction; develops topics coherently and appropriately."
        elif wpm >= 98 and filler_ratio <= 3.5:
            band = 7.0
            summary = "Speaks at length without noticeable effort; uses a range of connectives and discourse markers flexibly."
        elif (wpm >= 75 and filler_ratio <= 3.0) or (wpm >= 85 and filler_ratio <= 5.5):
            band = 6.0
            summary = "Willing to speak at length, though may lose coherence at times due to occasional repetition or hesitation."
        elif wpm >= 55:
            band = 5.0
            summary = "Usually maintains flow of speech but uses repetition and self-correction to keep going; overuses simple connectives."
        else:
            band = 4.0
            summary = "Cannot respond without noticeable pauses and speaks slowly with frequent breakdown in coherence."

        # Collect evidence & strengths
        if wpm >= 115:
            strengths.append(f"Maintained strong conversational momentum ({wpm} WPM).")
        else:
            improvements.append(f"Speech tempo ({wpm} WPM) is somewhat hesitant; target 125-145 WPM for higher bands.")

        if markers_count >= 3:
            strengths.append(f"Utilized cohesive discourse markers effectively: {', '.join(metrics.discourse_markers[:4])}.")
        else:
            improvements.append("Incorporate more varied transitional markers (e.g., 'furthermore', 'on the other hand', 'consequently').")

        if filler_ratio <= 2.0:
            strengths.append("Very low reliance on filled pauses ('um', 'uh').")
        else:
            improvements.append(f"Filled pause density is {filler_ratio}%; try replacing 'um/uh' with brief silent pauses.")

        # Cited evidence samples
        sentences = [s.strip() for s in full_text.split(".") if len(s.strip()) > 30]
        if sentences:
            evidence = sentences[:2]

        return CriterionScore(
            criterion_name="Fluency and Coherence",
            band=band,
            descriptor_summary=summary,
            strengths=strengths,
            areas_for_improvement=improvements,
            cited_evidence=evidence
        )
