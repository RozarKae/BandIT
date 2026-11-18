"""
Data models for the IELTS Scoring and Calibration Engine.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import datetime


@dataclass
class CriterionScore:
    criterion_name: str  # e.g., "Fluency and Coherence"
    band: float  # Official IELTS scale (0.0 to 9.0, increments of 0.5)
    descriptor_summary: str
    strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    cited_evidence: List[str] = field(default_factory=list)


@dataclass
class FluencyMetrics:
    total_words: int
    speaking_duration_seconds: float
    words_per_minute: float
    filler_word_count: int
    filler_words: List[str]
    filler_frequency_percent: float
    discourse_markers: List[str]
    discourse_marker_count: int
    estimated_pause_ratio: float


@dataclass
class LexicalMetrics:
    total_tokens: int
    unique_tokens: int
    type_token_ratio: float  # TTR
    cefr_distribution: Dict[str, float]  # {"A1_A2": 50.0, "B1_B2": 35.0, "C1_C2": 15.0}
    academic_words_used: List[str]
    sophisticated_collocations: List[str]
    overused_words: List[str]


@dataclass
class GrammarMetrics:
    total_sentences: int
    simple_sentence_count: int
    compound_sentence_count: int
    complex_sentence_count: int
    complex_sentence_ratio: float
    conditionals_used: List[str]
    passives_used: List[str]
    relative_clauses_used: List[str]
    detected_errors: List[Dict[str, str]]  # {"error": ..., "correction": ..., "rule": ...}


@dataclass
class PronunciationMetrics:
    intelligibility_score: float  # 0 to 100
    syllable_stress_accuracy: float  # 0 to 100
    rhythm_and_chunking_score: float  # 0 to 100
    challenging_phonemes: List[str]


@dataclass
class SentenceUpgrade:
    original: str
    upgraded: str
    target_band: float
    linguistic_rationale: str


@dataclass
class IELTSFullScorecard:
    session_id: str
    candidate_name: str
    test_theme: str
    evaluated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    # Official 4-Criterion Bands
    overall_band: float = 0.0
    fluency_and_coherence: Optional[CriterionScore] = None
    lexical_resource: Optional[CriterionScore] = None
    grammatical_range_and_accuracy: Optional[CriterionScore] = None
    pronunciation: Optional[CriterionScore] = None
    
    # Quantitative Analytics
    fluency_metrics: Optional[FluencyMetrics] = None
    lexical_metrics: Optional[LexicalMetrics] = None
    grammar_metrics: Optional[GrammarMetrics] = None
    pronunciation_metrics: Optional[PronunciationMetrics] = None
    
    # Actionable Feedback
    sentence_upgrades: List[SentenceUpgrade] = field(default_factory=list)
    examiner_overall_summary: str = ""
    personalized_action_plan: List[str] = field(default_factory=list)
