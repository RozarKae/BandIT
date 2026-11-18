"""
Master Scoring Pipeline for IELTS Speaking Examination.
Coordinates speech analytics, lexical/grammar profilers, and calibrators into an official IELTS scorecard.
"""

from typing import Dict, Any, Optional
from scoring_engine.models import (
    IELTSFullScorecard,
    CriterionScore
)
from scoring_engine.fluency_analyzer import FluencyAnalyzer
from scoring_engine.lexical_analyzer import LexicalAnalyzer
from scoring_engine.grammar_analyzer import GrammarAnalyzer
from scoring_engine.pronunciation_analyzer import PronunciationAnalyzer
from scoring_engine.score_calibrator import ScoreCalibrator
from scoring_engine.report_generator import ReportGenerator
from scoring_engine.llm_evaluator import MultiAgentLLMEvaluator


class IELTSScoringPipeline:
    """
    End-to-end evaluation pipeline for IELTS Speaking interview transcripts and audio features.
    Fuses deterministic acoustic/NLP analytics with live frontier LLM examiner evaluations.
    """

    @classmethod
    def evaluate_session(
        cls,
        session_payload: Dict[str, Any],
        acoustic_features: Optional[Dict[str, Any]] = None,
        use_llm: bool = True
    ) -> IELTSFullScorecard:
        """
        Evaluate a complete IELTS speaking session payload.
        """
        transcript = session_payload.get("transcript", [])
        candidate_turns = [
            turn for turn in transcript
            if turn.get("speaker") == "CANDIDATE" and turn.get("stage") != "PART1_ID_CHECK"
        ]

        if not candidate_turns:
            raise ValueError("No valid candidate speech turns found in the session payload.")

        # 1. Deterministic NLP & Acoustic Feature Extraction
        f_metrics, fc_score = FluencyAnalyzer.analyze(candidate_turns)
        l_metrics, lr_score = LexicalAnalyzer.analyze(candidate_turns)
        g_metrics, gra_score = GrammarAnalyzer.analyze(candidate_turns)
        p_metrics, pr_score = PronunciationAnalyzer.analyze(candidate_turns, acoustic_features)

        deterministic_summary = {
            "wpm": f_metrics.words_per_minute,
            "ttr": l_metrics.type_token_ratio,
            "cefr_distribution": l_metrics.cefr_distribution,
            "filler_ratio": f_metrics.filler_frequency_percent,
            "complex_sentence_ratio": g_metrics.complex_sentence_ratio,
            "intelligibility_score": p_metrics.intelligibility_score
        }

        # 2. Live Frontier LLM Evaluation (or calibrated arbitrator)
        sentence_upgrades = []
        action_plan = []

        if use_llm:
            try:
                llm_eval = MultiAgentLLMEvaluator.evaluate_session_with_llm(
                    candidate_turns, deterministic_summary
                )

                if "fluency_and_coherence" in llm_eval:
                    fc_data = llm_eval["fluency_and_coherence"]
                    fc_score.band = float(fc_data.get("band", fc_score.band))
                    if fc_data.get("summary"):
                        fc_score.descriptor_summary = fc_data["summary"]
                    if fc_data.get("strengths"):
                        fc_score.strengths = fc_data["strengths"]
                    if fc_data.get("improvements"):
                        fc_score.areas_for_improvement = fc_data["improvements"]
                    if fc_data.get("cited_evidence"):
                        fc_score.cited_evidence = fc_data["cited_evidence"]

                if "lexical_resource" in llm_eval:
                    lr_data = llm_eval["lexical_resource"]
                    lr_score.band = float(lr_data.get("band", lr_score.band))
                    if lr_data.get("summary"):
                        lr_score.descriptor_summary = lr_data["summary"]
                    if lr_data.get("strengths"):
                        lr_score.strengths = lr_data["strengths"]
                    if lr_data.get("improvements"):
                        lr_score.areas_for_improvement = lr_data["improvements"]
                    if lr_data.get("cited_evidence"):
                        lr_score.cited_evidence = lr_data["cited_evidence"]

                if "grammatical_range_and_accuracy" in llm_eval:
                    gra_data = llm_eval["grammatical_range_and_accuracy"]
                    gra_score.band = float(gra_data.get("band", gra_score.band))
                    if gra_data.get("summary"):
                        gra_score.descriptor_summary = gra_data["summary"]
                    if gra_data.get("strengths"):
                        gra_score.strengths = gra_data["strengths"]
                    if gra_data.get("improvements"):
                        gra_score.areas_for_improvement = gra_data["improvements"]
                    if gra_data.get("cited_evidence"):
                        gra_score.cited_evidence = gra_data["cited_evidence"]

                if "pronunciation" in llm_eval:
                    pr_data = llm_eval["pronunciation"]
                    pr_score.band = float(pr_data.get("band", pr_score.band))
                    if pr_data.get("summary"):
                        pr_score.descriptor_summary = pr_data["summary"]
                    if pr_data.get("strengths"):
                        pr_score.strengths = pr_data["strengths"]
                    if pr_data.get("improvements"):
                        pr_score.areas_for_improvement = pr_data["improvements"]
                    if pr_data.get("cited_evidence"):
                        pr_score.cited_evidence = pr_data["cited_evidence"]

                # Extract upgrades & action plan from LLM output
                if "sentence_upgrades" in llm_eval:
                    sentence_upgrades = [
                        ScoreCalibrator.generate_sentence_upgrades(candidate_turns)[0]
                        if not isinstance(u, dict) else
                        # Wrap into SentenceUpgrade
                        type("Upgrade", (), {
                            "original": u.get("original", ""),
                            "upgraded": u.get("upgraded", ""),
                            "target_band": float(u.get("target_band", 8.5)),
                            "linguistic_rationale": u.get("rationale", "")
                        })()
                        for u in llm_eval["sentence_upgrades"]
                    ]

                if "action_plan" in llm_eval and isinstance(llm_eval["action_plan"], list):
                    action_plan = llm_eval["action_plan"]

            except Exception as e:
                print(f"LLM synthesis notice: {e}, using calibrated fallback.")

        # If LLM didn't produce upgrades/plan, generate via deterministic rules
        if not sentence_upgrades:
            sentence_upgrades = ScoreCalibrator.generate_sentence_upgrades(candidate_turns)
        if not action_plan:
            action_plan = ScoreCalibrator.generate_personalized_action_plan(
                fc_band=fc_score.band,
                lr_band=lr_score.band,
                gra_band=gra_score.band,
                pr_band=pr_score.band
            )

        # 3. Overall Band Calculation with IELTS Half-Band Rounding Rules
        overall_band = ScoreCalibrator.calculate_ielts_overall_band(
            fc=fc_score.band,
            lr=lr_score.band,
            gra=gra_score.band,
            pr=pr_score.band
        )

        # 7. Construct Full Scorecard
        scorecard = IELTSFullScorecard(
            session_id=session_payload.get("session_id", "unknown"),
            candidate_name=session_payload.get("candidate_name", "Candidate"),
            test_theme=session_payload.get("test_theme", "IELTS Speaking"),
            overall_band=overall_band,
            fluency_and_coherence=fc_score,
            lexical_resource=lr_score,
            grammatical_range_and_accuracy=gra_score,
            pronunciation=pr_score,
            fluency_metrics=f_metrics,
            lexical_metrics=l_metrics,
            grammar_metrics=g_metrics,
            pronunciation_metrics=p_metrics,
            sentence_upgrades=sentence_upgrades,
            personalized_action_plan=action_plan
        )

        return scorecard

    @classmethod
    def evaluate_and_generate_report(
        cls,
        session_payload: Dict[str, Any],
        acoustic_features: Optional[Dict[str, Any]] = None
    ) -> str:
        """Evaluate session and return Markdown formatted report."""
        scorecard = cls.evaluate_session(session_payload, acoustic_features)
        return ReportGenerator.to_markdown(scorecard)
