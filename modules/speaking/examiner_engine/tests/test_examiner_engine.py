"""
Unit tests for the IELTS Speaking Examiner Engine & State Machine.
"""

import unittest
import sys
import os

# Add package root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from examiner_engine.models import ExamStage, Speaker
from examiner_engine.question_bank import TEST_SET_1, get_all_test_sets, get_test_set_by_id
from examiner_engine.state_machine import IELTSExaminerSession
from examiner_engine.examiner_persona import ExaminerPersonaHelper


class TestIELTSExaminerEngine(unittest.TestCase):

    def setUp(self):
        self.test_set = TEST_SET_1
        self.session = IELTSExaminerSession(test_set=self.test_set, candidate_name="Jane Doe")

    def test_question_bank_loading(self):
        """Verify question bank loads and contains valid test sets."""
        all_sets = get_all_test_sets()
        self.assertGreaterEqual(len(all_sets), 3)
        found = get_test_set_by_id(self.test_set.id)
        self.assertIsNotNone(found)
        self.assertEqual(len(found.part1_questions), 4)
        self.assertEqual(len(found.part3_questions), 3)

    def test_full_mock_test_flow(self):
        """Simulate a complete end-to-end IELTS mock interview."""
        # 1. Greeting
        action = self.session.start_exam()
        self.assertEqual(action.stage, ExamStage.PART1_ID_CHECK)
        self.assertTrue(action.requires_candidate_input)
        self.assertIn("speaking test for the International English Language Testing System", action.utterance)

        # 2. Candidate ID verification response
        action = self.session.handle_candidate_response("My name is Jane Doe, and you can call me Jane.", duration_seconds=5.0)
        self.assertEqual(action.stage, ExamStage.PART1_QUESTIONS)
        self.assertIn("Mobile Phones & Apps", action.utterance)

        # 3. Part 1 Questions iteration (4 questions)
        for i in range(len(self.test_set.part1_questions)):
            # Candidate answers
            answer_text = "I use mobile applications mostly for productivity, scheduling, and navigation every day."
            action = self.session.handle_candidate_response(answer_text, duration_seconds=20.0)

            if i < len(self.test_set.part1_questions) - 1:
                self.assertEqual(action.stage, ExamStage.PART1_QUESTIONS)
            else:
                # Should transition to Part 2 cue card
                self.assertEqual(action.stage, ExamStage.PART2_PREPARATION)
                self.assertIsNotNone(action.display_cue_card)
                self.assertEqual(action.timer_countdown_seconds, 60)

        # 4. Part 2 Preparation completion
        action = self.session.trigger_part2_prep_finished()
        self.assertEqual(action.stage, ExamStage.PART2_SPEAKING)
        self.assertIn("Your one minute preparation is up", action.utterance)

        # 5. Part 2 Monologue (e.g., candidate speaks for 110s)
        monologue = (
            "I would like to speak about Notion, an application that completely transformed my academic workflow. "
            "I first discovered it during my university days when balancing multiple research projects was overwhelming. "
            "It provided a modular database system that allowed me to organize notes, citations, and daily deadlines. "
            "It has made a profound difference because it eliminated mental clutter and helped me stay structured."
        )
        action = self.session.handle_candidate_response(monologue, duration_seconds=110.0)
        self.assertEqual(action.stage, ExamStage.PART2_ROUND_OFF)

        # 6. Part 2 Round-off questions
        action = self.session.handle_candidate_response("Yes, most of my university peers also use it.", duration_seconds=8.0)
        action = self.session.handle_candidate_response("I certainly think so, as long as they keep innovating.", duration_seconds=10.0)

        # 7. Part 3 Discussion Questions
        self.assertEqual(action.stage, ExamStage.PART3_DISCUSSION)
        self.assertIn("We've been talking about", action.utterance)

        # Candidate answers Part 3 Q1 with rich answer
        action = self.session.handle_candidate_response(
            "While automation will undoubtedly displace repetitive manual and computational tasks, "
            "I believe creative strategy and empathetic human care cannot be replicated by algorithms. "
            "Consequently, the job market will evolve rather than collapse.",
            duration_seconds=42.0
        )
        self.assertEqual(action.stage, ExamStage.PART3_DISCUSSION)

        # Candidate answers Part 3 Q2 briefly (triggering adaptive probe!)
        action = self.session.handle_candidate_response(
            "Governments should run community training programs.",
            duration_seconds=5.0
        )
        # Should trigger dynamic probe because it was too short and lacked justification
        self.assertEqual(action.stage, ExamStage.PART3_DISCUSSION)
        self.assertIn("Why do you think that is the case?", action.utterance)

        # Candidate elaborates on the probe
        action = self.session.handle_candidate_response(
            "Because senior citizens often struggle with smartphone touch interfaces and need patient in-person guidance.",
            duration_seconds=22.0
        )

        # Candidate answers Part 3 Q3 (last question)
        action = self.session.handle_candidate_response(
            "Unfortunately yes, people often trade data privacy for seamless convenience, "
            "as clicking 'accept all cookies' requires much less mental effort than reading lengthy legal policies.",
            duration_seconds=38.0
        )

        # 8. Exam Completion
        self.assertEqual(action.stage, ExamStage.COMPLETED)
        self.assertIn("That is the end of the speaking test", action.utterance)
        self.assertFalse(action.requires_candidate_input)

        # 9. Verify Payload Export for Scoring Engine
        payload = self.session.export_session_payload()
        self.assertEqual(payload["candidate_name"], "Jane Doe")
        self.assertEqual(payload["test_set_id"], self.test_set.id)
        self.assertGreater(len(payload["transcript"]), 15)
        # Verify speakers are alternately recorded
        speakers = [e["speaker"] for e in payload["transcript"]]
        self.assertIn(Speaker.EXAMINER.value, speakers)
        self.assertIn(Speaker.CANDIDATE.value, speakers)

    def test_response_depth_heuristics(self):
        """Test heuristic evaluation of response depth."""
        # Too short
        eval_short = ExaminerPersonaHelper.evaluate_response_depth("Yes, I do.", duration_seconds=2.0)
        self.assertEqual(eval_short, "TOO_SHORT")

        # Optimal
        eval_opt = ExaminerPersonaHelper.evaluate_response_depth(
            "I definitely prefer calling because tone of voice eliminates misunderstandings.",
            duration_seconds=15.0
        )
        self.assertEqual(eval_opt, "OPTIMAL")

        # Too long
        long_text = "word " * 105
        eval_long = ExaminerPersonaHelper.evaluate_response_depth(long_text, duration_seconds=55.0)
        self.assertEqual(eval_long, "TOO_LONG")


if __name__ == "__main__":
    unittest.main()
