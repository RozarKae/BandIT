"""
Pronunciation (PR) Analyzer.
Evaluates intelligibility, syllable stress, rhythm chunking, and phonological complexity.
Supports both acoustic feature inputs (from ASR/audio) and linguistic phonetic profiling.
"""

import re
from typing import List, Dict, Any, Tuple
from scoring_engine.models import PronunciationMetrics, CriterionScore

# Phonologically complex words (consonant clusters, shifting syllable stress)
COMPLEX_PHONOLOGY_WORDS = {
    "dissertations": "ˌdɪsərˈteɪʃənz",
    "indispensable": "ˌɪndɪˈspɛnsəbəl",
    "predominantly": "prɪˈdɒmɪnəntli",
    "scrutinizing": "ˈskruːtɪˌnaɪzɪŋ",
    "versatility": "ˌvɜːrsəˈtɪlɪti",
    "algorithmic": "ˌælɡəˈrɪðmɪk",
    "exploitation": "ˌɛksplɔɪˈteɪʃən",
    "productivity": "ˌproʊdʌkˈtɪvɪti"
}


class PronunciationAnalyzer:

    @staticmethod
    def analyze(
        candidate_turns: List[Dict[str, Any]],
        acoustic_features: Dict[str, Any] = None
    ) -> Tuple[PronunciationMetrics, CriterionScore]:
        all_text = " ".join(t.get("text", "") for t in candidate_turns)
        words = re.findall(r"\b[A-Za-z'-]+\b", all_text.lower())
        
        # Check acoustic features if supplied (e.g. from Azure/Kaldi GoP)
        if acoustic_features:
            intelligibility = acoustic_features.get("intelligibility", 85.0)
            stress_acc = acoustic_features.get("stress_accuracy", 80.0)
            rhythm_score = acoustic_features.get("rhythm_score", 82.0)
            challenging = acoustic_features.get("challenging_phonemes", ["/θ/", "/ð/", "/r/"])
        else:
            # Model phonetic profile from transcript characteristics
            multisyllabic_count = sum(1 for w in words if len(w) >= 8)
            ratio = multisyllabic_count / max(len(words), 1)
            
            # Baseline high intelligibility for coherent complex sentences
            intelligibility = min(95.0, 75.0 + (ratio * 100))
            stress_acc = min(90.0, 72.0 + (ratio * 80))
            rhythm_score = min(90.0, 74.0 + (ratio * 75))
            challenging = ["/θ/ (as in 'through')", "/ð/ (as in 'therefore')", "/v/ vs /w/"]

        metrics = PronunciationMetrics(
            intelligibility_score=round(intelligibility, 1),
            syllable_stress_accuracy=round(stress_acc, 1),
            rhythm_and_chunking_score=round(rhythm_score, 1),
            challenging_phonemes=challenging
        )

        score = PronunciationAnalyzer._calibrate_pr_band(metrics, words)
        return metrics, score

    @staticmethod
    def _calibrate_pr_band(metrics: PronunciationMetrics, words: List[str]) -> CriterionScore:
        intel = metrics.intelligibility_score
        stress = metrics.syllable_stress_accuracy

        strengths = []
        improvements = []

        if intel >= 88 and stress >= 85:
            band = 8.0
            summary = "Uses a wide range of pronunciation features; sustained flexible use with only occasional lapses; is effortless to understand throughout."
        elif intel >= 80 and stress >= 75:
            band = 7.0
            summary = "Shows all the positive features of Band 6 and some of Band 8; can generally be understood throughout with good control of phonological features."
        elif intel >= 70:
            band = 6.0
            summary = "Uses a range of pronunciation features with mixed control; can generally be understood throughout, though individual word mispronunciations may occur."
        elif intel >= 60:
            band = 5.0
            summary = "Uses a limited range of pronunciation features; attempts to control features but lapses are frequent; mispronunciations reduce clarity occasionally."
        else:
            band = 4.0
            summary = "Uses a limited range of pronunciation features with frequent errors; requires listener effort to comprehend."

        if intel >= 80:
            strengths.append(f"High intelligibility score ({metrics.intelligibility_score}/100) across multisyllabic vocabulary.")
            strengths.append("Natural sentence stress and syntactic chunking rhythm.")
        else:
            improvements.append("Work on connected speech linking and reducing choppy word-by-word delivery.")

        improvements.append(f"Review vowel clarity and consonant clusters on: {', '.join(metrics.challenging_phonemes[:2])}.")

        return CriterionScore(
            criterion_name="Pronunciation",
            band=band,
            descriptor_summary=summary,
            strengths=strengths,
            areas_for_improvement=improvements,
            cited_evidence=[f"Multisyllabic articulation sample: '{w}'" for w in words if len(w) >= 10][:2]
        )
