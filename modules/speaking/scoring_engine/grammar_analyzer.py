"""
Grammatical Range and Accuracy (GRA) Analyzer.
Analyzes sentence structures, syntactic variety (complex vs compound), conditionals, passives, and grammatical errors.
"""

import re
from typing import List, Dict, Any, Tuple
from scoring_engine.models import GrammarMetrics, CriterionScore

SUBORDINATING_CONJUNCTIONS = [
    r"\balthough\b", r"\beven though\b", r"\bwhereas\b", r"\bwhile\b",
    r"\bbecause\b", r"\bsince\b", r"\bunless\b", r"\bprovided that\b",
    r"\bas long as\b", r"\bso that\b", r"\bin order that\b", r"\bdespite the fact that\b",
    r"\bwhen\b", r"\bwhenever\b", r"\bbefore\b", r"\bafter\b", r"\bwhether\b",
    r"\bwhich\b", r"\bwho\b", r"\bwhose\b", r"\bwhere\b"
]

COORDINATING_CONJUNCTIONS = [
    r"\band\b", r"\bbut\b", r"\bso\b", r"\byet\b", r"\bfor\b"
]

PASSIVE_PATTERNS = [
    r"\b(is|are|was|were|been|being)\s+([a-z]+ed|built|made|written|done|seen|found|given|taken|lost|held)\b"
]

CONDITIONAL_PATTERNS = [
    r"\bif\b.+\b(would|could|might|will)\b",
    r"\bunless\b.+\b(would|could|might|will)\b",
    r"\bhad\b.+\bwould have\b"
]

RELATIVE_CLAUSE_PATTERNS = [
    r"\b(which|that|who|whose|where|whom)\s+[a-z]+",
]

COMMON_ERROR_PATTERNS = [
    (r"\b(he|she|it)\s+(don't|have|go|want|like|do|make)\b", "Subject-verb agreement error with 3rd person singular."),
    (r"\b(they|we|you)\s+(is|was)\b", "Subject-verb agreement error with plural subject."),
    (r"\bmore\s+(better|faster|cheaper|easier|harder)\b", "Double comparative form error."),
    (r"\bexplain\s+me\b", "Incorrect prepositional usage (should be 'explain to me')."),
    (r"\blisten\s+(the|music|people)\b", "Missing preposition 'to' after 'listen'.")
]


class GrammarAnalyzer:

    @staticmethod
    def analyze(candidate_turns: List[Dict[str, Any]]) -> Tuple[GrammarMetrics, CriterionScore]:
        all_text = " ".join(t.get("text", "") for t in candidate_turns)
        
        # Sentence splitting
        raw_sentences = [s.strip() for s in re.split(r"[.!?]+", all_text) if len(s.strip().split()) >= 4]
        total_sentences = max(len(raw_sentences), 1)

        complex_sentences = []
        compound_sentences = []
        simple_sentences = []

        conditionals_found = []
        passives_found = []
        relative_clauses_found = []
        detected_errors = []

        for sentence in raw_sentences:
            s_lower = sentence.lower()
            
            # Check complex
            is_complex = any(re.search(pat, s_lower) for pat in SUBORDINATING_CONJUNCTIONS)
            # Check compound
            is_compound = any(re.search(pat, s_lower) for pat in COORDINATING_CONJUNCTIONS)

            if is_complex:
                complex_sentences.append(sentence)
            elif is_compound:
                compound_sentences.append(sentence)
            else:
                simple_sentences.append(sentence)

            # Check conditionals
            for c_pat in CONDITIONAL_PATTERNS:
                if re.search(c_pat, s_lower):
                    conditionals_found.append(sentence)
                    break

            # Check passive voice
            for p_pat in PASSIVE_PATTERNS:
                m = re.search(p_pat, s_lower)
                if m:
                    passives_found.append(m.group(0))

            # Check relative clauses
            for r_pat in RELATIVE_CLAUSE_PATTERNS:
                if re.search(r_pat, s_lower):
                    relative_clauses_found.append(sentence)
                    break

            # Check common errors
            for err_pat, explanation in COMMON_ERROR_PATTERNS:
                err_match = re.search(err_pat, s_lower)
                if err_match:
                    detected_errors.append({
                        "error": err_match.group(0),
                        "sentence": sentence,
                        "rule": explanation
                    })

        complex_ratio = round(len(complex_sentences) / total_sentences, 2)

        metrics = GrammarMetrics(
            total_sentences=total_sentences,
            simple_sentence_count=len(simple_sentences),
            compound_sentence_count=len(compound_sentences),
            complex_sentence_count=len(complex_sentences),
            complex_sentence_ratio=complex_ratio,
            conditionals_used=conditionals_found,
            passives_used=list(set(passives_found)),
            relative_clauses_used=relative_clauses_found,
            detected_errors=detected_errors
        )

        score = GrammarAnalyzer._calibrate_gra_band(metrics, raw_sentences)
        return metrics, score

    @staticmethod
    def _calibrate_gra_band(metrics: GrammarMetrics, sentences: List[str]) -> CriterionScore:
        c_ratio = metrics.complex_sentence_ratio
        err_count = len(metrics.detected_errors)
        passives_count = len(metrics.passives_used)
        conditionals_count = len(metrics.conditionals_used)

        strengths = []
        improvements = []

        # Band Calibration against IELTS Band Descriptors
        if c_ratio >= 0.40 and err_count == 0:
            band = 8.0
            summary = "Uses a wide range of complex structures flexibly; the majority of sentences are error-free with only very occasional non-systematic slips."
        elif c_ratio >= 0.30 and err_count <= 1:
            band = 7.0
            summary = "Uses a range of complex structures with good control and flexibility; frequently produces error-free sentences."
        elif c_ratio >= 0.18:
            band = 6.0
            summary = "Uses a mix of simple and complex structures, but with limited flexibility; may make occasional errors though they do not impede communication."
        elif c_ratio >= 0.10:
            band = 5.0
            summary = "Produces basic sentence forms with reasonable accuracy; uses a limited range of more complex structures which often contain errors."
        else:
            band = 4.0
            summary = "Produces basic sentence forms and some correct simple sentences, but subordinate clauses are rare and errors predominate."

        # Strengths & Observations
        if c_ratio >= 0.30:
            strengths.append(f"Strong syntactic variety with {int(c_ratio * 100)}% of utterances utilizing subordinate or complex clauses.")
        if passives_count > 0:
            strengths.append(f"Effective use of passive structures (e.g., '{metrics.passives_used[0]}').")
        if conditionals_count > 0:
            strengths.append("Successfully integrated hypothetical/conditional sentence structures.")

        if err_count > 0:
            improvements.append(f"Watch out for grammar slips: {metrics.detected_errors[0]['rule']}")
        if c_ratio < 0.30:
            improvements.append("Increase usage of complex sentence linkers (e.g., 'although', 'whereas', 'provided that') rather than chaining simple clauses with 'and/so'.")

        evidence = [s for s in sentences if len(s.split()) > 10][:2]

        return CriterionScore(
            criterion_name="Grammatical Range and Accuracy",
            band=band,
            descriptor_summary=summary,
            strengths=strengths,
            areas_for_improvement=improvements,
            cited_evidence=evidence
        )
