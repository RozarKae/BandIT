"""
Lexical Resource (LR) Analyzer.
Evaluates vocabulary range, CEFR level distribution, collocations, idiomaticity, and repetition.
"""

import re
from typing import List, Dict, Any, Tuple, Set
from scoring_engine.models import LexicalMetrics, CriterionScore

# Built-in reference lists for CEFR classification and Academic Word List
C1_C2_WORDS = {
    "versatility", "indispensable", "predominantly", "scrutinizing", "displace",
    "rapport", "mindlessly", "non-intrusive", "subtle", "empower", "inequality",
    "disproportionately", "ubiquitous", "mitigate", "paradigm", "resilient",
    "sophisticated", "unprecedented", "profound", "dissertation", "coursework",
    "algorithmic", "scrutinize", "indispensability", "dichotomy", "ambiguity",
    "counterproductive", "paramount", "pivotal", "consequently", "nevertheless",
    "intimidate", "exclusion", "exploit", "exploitation", "matrix", "versatile"
}

B1_B2_WORDS = {
    "application", "productivity", "routine", "convenient", "logistical", "casual",
    "emotional", "connection", "academic", "database", "analytical", "eliminate",
    "advancement", "sacrifice", "privacy", "invest", "initiative", "participate",
    "conservation", "sustainable", "expansion", "incentivize", "infrastructure",
    "monument", "architectural", "transportation", "congestion", "overcrowding",
    "isolated", "suburban", "technological", "significant", "organize", "eliminate"
}

SOPHISTICATED_COLLOCATIONS = [
    "emotional intelligence", "non-verbal cues", "face-to-face", "without doubt",
    "mindlessly scrolling", "genuine rapport", "save hours of stress",
    "critical judgment", "trade privacy for convenience", "terms of service",
    "prevent digital exclusion", "rapid advancements", "academic productivity",
    "literature review", "data protection", "commercial exploitation",
    "daily routine", "lifestyle choices", "sustainable practices", "public transit"
]

GENERIC_OVERUSED_WORDS = {"good", "bad", "big", "thing", "things", "stuff", "very", "a lot"}


class LexicalAnalyzer:

    @staticmethod
    def analyze(candidate_turns: List[Dict[str, Any]]) -> Tuple[LexicalMetrics, CriterionScore]:
        all_text = " ".join(t.get("text", "") for t in candidate_turns)
        raw_tokens = re.findall(r"\b[A-Za-z'-]+\b", all_text.lower())
        total_tokens = len(raw_tokens)
        
        # Unique tokens & Type-Token Ratio
        unique_tokens_set = set(raw_tokens)
        unique_tokens_count = len(unique_tokens_set)
        ttr = round(unique_tokens_count / max(total_tokens, 1), 3)

        # CEFR Classification
        c1_c2_count = sum(1 for w in raw_tokens if w in C1_C2_WORDS)
        b1_b2_count = sum(1 for w in raw_tokens if w in B1_B2_WORDS)
        a1_a2_count = max(0, total_tokens - (c1_c2_count + b1_b2_count))

        cefr_dist = {
            "A1_A2": round((a1_a2_count / max(total_tokens, 1)) * 100, 1),
            "B1_B2": round((b1_b2_count / max(total_tokens, 1)) * 100, 1),
            "C1_C2": round((c1_c2_count / max(total_tokens, 1)) * 100, 1)
        }

        # Academic words and high-level collocations detected
        academic_found = sorted(list(unique_tokens_set.intersection(C1_C2_WORDS)))
        
        text_lower = all_text.lower()
        collocations_found = [c for c in SOPHISTICATED_COLLOCATIONS if c in text_lower]

        # Overused words check
        word_frequencies = {}
        for w in raw_tokens:
            if w in GENERIC_OVERUSED_WORDS:
                word_frequencies[w] = word_frequencies.get(w, 0) + 1
        
        overused = [w for w, count in word_frequencies.items() if count >= 3]

        metrics = LexicalMetrics(
            total_tokens=total_tokens,
            unique_tokens=unique_tokens_count,
            type_token_ratio=ttr,
            cefr_distribution=cefr_dist,
            academic_words_used=academic_found,
            sophisticated_collocations=collocations_found,
            overused_words=overused
        )

        score = LexicalAnalyzer._calibrate_lr_band(metrics, all_text)
        return metrics, score

    @staticmethod
    def _calibrate_lr_band(metrics: LexicalMetrics, full_text: str) -> CriterionScore:
        ttr = metrics.type_token_ratio
        c1_c2_pct = metrics.cefr_distribution["C1_C2"]
        collocations_count = len(metrics.sophisticated_collocations)
        overused_count = len(metrics.overused_words)

        strengths = []
        improvements = []

        # Band Calibration against IELTS Band Descriptors
        if c1_c2_pct >= 4.0 and collocations_count >= 5 and overused_count == 0 and ttr >= 0.45:
            band = 8.0
            summary = "Uses a wide, sophisticated vocabulary resource readily and flexibly to convey precise meaning; skillful use of uncommon and idiomatic items."
        elif (c1_c2_pct >= 2.0 or collocations_count >= 3) and ttr >= 0.38:
            band = 7.0
            summary = "Uses vocabulary resource flexibly to discuss a variety of topics; uses some less common and idiomatic vocabulary with awareness of style and collocation."
        elif ttr >= 0.30:
            band = 6.0
            summary = "Has a wide enough vocabulary to discuss topics at length and make meaning clear; generally successful use of vocabulary despite some inappropriacies."
        elif ttr >= 0.22:
            band = 5.0
            summary = "Manages to talk about familiar and unfamiliar topics but uses vocabulary with limited flexibility; attempts paraphrase with mixed success."
        else:
            band = 4.0
            summary = "Uses limited vocabulary, sufficient only for simple information; frequent repetition and errors in word choice."

        # Strengths & Observations
        if metrics.academic_words_used:
            strengths.append(f"Demonstrated advanced C1/C2 lexical items: {', '.join(metrics.academic_words_used[:5])}.")
        if collocations_count >= 2:
            strengths.append(f"Employed natural idiomatic collocations: {', '.join(metrics.sophisticated_collocations[:3])}.")

        if overused_count > 0:
            improvements.append(f"Reduce reliance on repetitive basic descriptors like: {', '.join(metrics.overused_words)}.")
        if c1_c2_pct < 2.5:
            improvements.append("Aim to weave in more precise topic-specific academic vocabulary instead of general conversational phrases.")

        evidence = [f"'{c}'" for c in metrics.sophisticated_collocations[:3]]

        return CriterionScore(
            criterion_name="Lexical Resource",
            band=band,
            descriptor_summary=summary,
            strengths=strengths,
            areas_for_improvement=improvements,
            cited_evidence=evidence
        )
