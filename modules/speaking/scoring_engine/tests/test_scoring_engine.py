"""
Unit tests for the IELTS Scoring and Calibration Engine.
"""

import unittest
import sys
import os
import json

# Add package root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scoring_engine.score_calibrator import ScoreCalibrator
from scoring_engine.fluency_analyzer import FluencyAnalyzer
from scoring_engine.lexical_analyzer import LexicalAnalyzer
from scoring_engine.grammar_analyzer import GrammarAnalyzer
from scoring_engine.pronunciation_analyzer import PronunciationAnalyzer
from scoring_engine.scoring_pipeline import IELTSScoringPipeline
from scoring_engine.report_generator import ReportGenerator


class TestIELTSScoringEngine(unittest.TestCase):

    def test_ielts_rounding_rules(self):
        """Test official IELTS half-band rounding logic."""
        # Exact integer
        self.assertEqual(ScoreCalibrator.calculate_ielts_overall_band(6.0, 6.0, 6.0, 6.0), 6.0)

        # Fraction .25 -> rounds up to .5
        self.assertEqual(ScoreCalibrator.calculate_ielts_overall_band(6.0, 6.5, 6.0, 6.5), 6.5)

        # Fraction .75 -> rounds up to next whole band
        self.assertEqual(ScoreCalibrator.calculate_ielts_overall_band(6.5, 6.5, 7.0, 7.0), 7.0)

        # Fraction < .25 -> rounds down to .0
        # Average = 24.5 / 4 = 6.125 -> rounds to 6.0
        self.assertEqual(ScoreCalibrator.calculate_ielts_overall_band(6.0, 6.0, 6.0, 6.5), 6.0)

        # Fraction between .25 and .75 (e.g. 6.375) -> rounds to .5
        # Average = 25.5 / 4 = 6.375 -> rounds to 6.5
        self.assertEqual(ScoreCalibrator.calculate_ielts_overall_band(6.5, 6.5, 6.5, 6.0), 6.5)

        # Average = 27.5 / 4 = 6.875 -> rounds to 7.0
        self.assertEqual(ScoreCalibrator.calculate_ielts_overall_band(7.0, 7.0, 7.0, 6.5), 7.0)

    def test_fluency_analyzer(self):
        """Verify speech rate, filler detection, and discourse marker extraction."""
        turns = [
            {
                "text": "Well, um, I definitely think that online communication is convenient, but on the other hand, face-to-face meetings build stronger bonds.",
                "duration_seconds": 12.0
            }
        ]
        metrics, score = FluencyAnalyzer.analyze(turns)
        self.assertGreater(metrics.words_per_minute, 50)
        self.assertGreaterEqual(metrics.filler_word_count, 1)
        self.assertIn("on the other hand", metrics.discourse_markers)
        self.assertIn(score.band, [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0])

    def test_lexical_analyzer(self):
        """Verify CEFR profiling, collocations, and TTR calculations."""
        turns = [
            {
                "text": "The versatility of this application is indispensable for academic productivity, allowing me to build genuine rapport."
            }
        ]
        metrics, score = LexicalAnalyzer.analyze(turns)
        self.assertGreater(metrics.type_token_ratio, 0.5)
        self.assertIn("indispensable", metrics.academic_words_used)
        self.assertIn("genuine rapport", metrics.sophisticated_collocations)
        self.assertGreaterEqual(score.band, 6.0)

    def test_grammar_analyzer(self):
        """Verify complex sentence identification and passive detection."""
        turns = [
            {
                "text": "Although technology offers unprecedented convenience, personal privacy was lost when data protection agreements were signed."
            }
        ]
        metrics, score = GrammarAnalyzer.analyze(turns)
        self.assertGreaterEqual(metrics.complex_sentence_count, 1)
        self.assertGreater(len(metrics.passives_used), 0)
        self.assertGreaterEqual(score.band, 6.5)

    def test_end_to_end_scoring_on_sample_payload(self):
        """Test full pipeline execution on the generated sample candidate transcript."""
        sample_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "examiner_engine", "sample_session_transcript.json"
        )
        self.assertTrue(os.path.exists(sample_path), "Sample transcript must exist.")

        with open(sample_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        scorecard = IELTSScoringPipeline.evaluate_session(payload)

        # Check candidate metadata
        self.assertEqual(scorecard.candidate_name, "Maria Silva")
        self.assertGreaterEqual(scorecard.overall_band, 6.5)
        self.assertLessEqual(scorecard.overall_band, 9.0)

        # Check 4 criteria
        for crit in [
            scorecard.fluency_and_coherence,
            scorecard.lexical_resource,
            scorecard.grammatical_range_and_accuracy,
            scorecard.pronunciation
        ]:
            self.assertIsNotNone(crit)
            self.assertGreaterEqual(crit.band, 6.0)
            self.assertTrue(len(crit.strengths) > 0)
            self.assertTrue(len(crit.descriptor_summary) > 10)

        # Check sentence upgrades
        self.assertGreaterEqual(len(scorecard.sentence_upgrades), 2)
        for up in scorecard.sentence_upgrades:
            self.assertGreater(up.target_band, 8.0)
            self.assertTrue(len(up.linguistic_rationale) > 10)

        # Check Markdown generation
        md_report = ReportGenerator.to_markdown(scorecard)
        self.assertIn("Official IELTS Speaking Diagnostic Report", md_report)
        self.assertIn("Overall Band Score:", md_report)
        self.assertIn("Band Upgrade Coaching", md_report)

        # Check JSON dict export
        json_dict = ReportGenerator.to_dict(scorecard)
        self.assertEqual(json_dict["candidate_name"], "Maria Silva")
        self.assertIn("criteria", json_dict)


if __name__ == "__main__":
    unittest.main()
