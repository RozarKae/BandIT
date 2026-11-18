"""
Diagnostic Report Generator for IELTS Speaking Evaluation.
Generates structured JSON and human-readable Markdown scorecards.
"""

from typing import Dict, Any
from scoring_engine.models import IELTSFullScorecard


class ReportGenerator:

    @staticmethod
    def to_markdown(scorecard: IELTSFullScorecard) -> str:
        fc = scorecard.fluency_and_coherence
        lr = scorecard.lexical_resource
        gra = scorecard.grammatical_range_and_accuracy
        pr = scorecard.pronunciation

        lines = [
            f"# Official IELTS Speaking Diagnostic Report",
            f"**Candidate:** {scorecard.candidate_name}  ",
            f"**Session ID:** `{scorecard.session_id}`  ",
            f"**Test Theme:** {scorecard.test_theme}  ",
            f"**Evaluation Date:** {scorecard.evaluated_at}  \n",
            f"---",
            f"## 🏆 Overall Band Score: **{scorecard.overall_band:.1f}** / 9.0\n",
            f"### Official Criteria Breakdown",
            f"| Criterion | Band Score | Descriptor Summary |",
            f"| :--- | :---: | :--- |",
            f"| **Fluency & Coherence (FC)** | **{fc.band:.1f}** | {fc.descriptor_summary} |",
            f"| **Lexical Resource (LR)** | **{lr.band:.1f}** | {lr.descriptor_summary} |",
            f"| **Grammatical Range & Accuracy (GRA)** | **{gra.band:.1f}** | {gra.descriptor_summary} |",
            f"| **Pronunciation (PR)** | **{pr.band:.1f}** | {pr.descriptor_summary} |\n",
            f"---",
            f"## 📊 Quantitative Analytics Summary\n",
            f"### 1. Fluency & Speech Tempo",
            f"- **Speech Rate:** {scorecard.fluency_metrics.words_per_minute} Words Per Minute (WPM)",
            f"- **Total Spoken Words:** {scorecard.fluency_metrics.total_words} words across {scorecard.fluency_metrics.speaking_duration_seconds}s",
            f"- **Filler Pause Density:** {scorecard.fluency_metrics.filler_frequency_percent}% (detected {scorecard.fluency_metrics.filler_word_count} filled pauses)",
            f"- **Cohesive Connectives:** {scorecard.fluency_metrics.discourse_marker_count} distinct discourse markers used\n",
            f"### 2. Lexical Breadth & Sophistication",
            f"- **Type-Token Ratio (TTR):** {scorecard.lexical_metrics.type_token_ratio} (vocabulary diversity index)",
            f"- **CEFR Classification:** A1-A2: `{scorecard.lexical_metrics.cefr_distribution['A1_A2']}%` | B1-B2: `{scorecard.lexical_metrics.cefr_distribution['B1_B2']}%` | C1-C2: `{scorecard.lexical_metrics.cefr_distribution['C1_C2']}%`",
            f"- **Advanced C1/C2 Lexical Items:** {', '.join(scorecard.lexical_metrics.academic_words_used) if scorecard.lexical_metrics.academic_words_used else 'None detected'}",
            f"- **Natural Collocations:** {', '.join(scorecard.lexical_metrics.sophisticated_collocations) if scorecard.lexical_metrics.sophisticated_collocations else 'None detected'}\n",
            f"### 3. Grammatical Complexity",
            f"- **Complex Sentence Ratio:** {int(scorecard.grammar_metrics.complex_sentence_ratio * 100)}% of candidate clauses",
            f"- **Passive Voice Usage:** {len(scorecard.grammar_metrics.passives_used)} instances ({', '.join(scorecard.grammar_metrics.passives_used)})",
            f"- **Grammar Errors Detected:** {len(scorecard.grammar_metrics.detected_errors)}\n",
            f"---",
            f"## 💡 Detailed Criterion Strengths & Areas for Improvement\n",
            f"### Fluency & Coherence",
            f"- **Strengths:** " + ("; ".join(fc.strengths) if fc.strengths else "Demonstrated baseline fluency."),
            f"- **To Improve:** " + ("; ".join(fc.areas_for_improvement) if fc.areas_for_improvement else "Consistently maintained conversational flow; continue sustaining this tempo."),
            f"\n### Lexical Resource",
            f"- **Strengths:** " + ("; ".join(lr.strengths) if lr.strengths else "Adequate vocabulary for task."),
            f"- **To Improve:** " + ("; ".join(lr.areas_for_improvement) if lr.areas_for_improvement else "Vocabulary was precise and appropriate; aim to explore even more diverse stylistic collocations."),
            f"\n### Grammatical Range & Accuracy",
            f"- **Strengths:** " + ("; ".join(gra.strengths) if gra.strengths else "Accurate basic clause structures."),
            f"- **To Improve:** " + ("; ".join(gra.areas_for_improvement) if gra.areas_for_improvement else "Zero systemic errors observed; maintain accurate syntactic flexibility."),
            f"\n### Pronunciation",
            f"- **Strengths:** " + ("; ".join(pr.strengths) if pr.strengths else "Intelligible delivery."),
            f"- **To Improve:** " + ("; ".join(pr.areas_for_improvement) if pr.areas_for_improvement else "High overall intelligibility; focus on native-like rhythm and tonic syllable stress."),
            f"\n---",
            f"## 🚀 Band Upgrade Coaching (Band 6.0 $\\to$ Band 8.5+ Examples)\n"
        ]

        for idx, up in enumerate(scorecard.sentence_upgrades, 1):
            lines.extend([
                f"#### Example {idx} (Target: Band {up.target_band})",
                f"> **Original:** \"{up.original}\"",
                f"> ",
                f"> **Upgraded Version:** \"{up.upgraded}\"",
                f"- **Why this scores higher:** {up.linguistic_rationale}\n"
            ])

        lines.extend([
            f"---",
            f"## 🎯 Actionable Study Plan\n"
        ])
        for step in scorecard.personalized_action_plan:
            lines.append(f"- {step}")

        return "\n".join(lines)

    @staticmethod
    def to_dict(scorecard: IELTSFullScorecard) -> Dict[str, Any]:
        """Convert scorecard object to a JSON-serializable dictionary."""
        return {
            "session_id": scorecard.session_id,
            "candidate_name": scorecard.candidate_name,
            "test_theme": scorecard.test_theme,
            "evaluated_at": scorecard.evaluated_at,
            "overall_band": scorecard.overall_band,
            "criteria": {
                "fluency_and_coherence": {
                    "band": scorecard.fluency_and_coherence.band,
                    "summary": scorecard.fluency_and_coherence.descriptor_summary,
                    "strengths": scorecard.fluency_and_coherence.strengths,
                    "improvements": scorecard.fluency_and_coherence.areas_for_improvement
                },
                "lexical_resource": {
                    "band": scorecard.lexical_resource.band,
                    "summary": scorecard.lexical_resource.descriptor_summary,
                    "strengths": scorecard.lexical_resource.strengths,
                    "improvements": scorecard.lexical_resource.areas_for_improvement
                },
                "grammatical_range_and_accuracy": {
                    "band": scorecard.grammatical_range_and_accuracy.band,
                    "summary": scorecard.grammatical_range_and_accuracy.descriptor_summary,
                    "strengths": scorecard.grammatical_range_and_accuracy.strengths,
                    "improvements": scorecard.grammatical_range_and_accuracy.areas_for_improvement
                },
                "pronunciation": {
                    "band": scorecard.pronunciation.band,
                    "summary": scorecard.pronunciation.descriptor_summary,
                    "strengths": scorecard.pronunciation.strengths,
                    "improvements": scorecard.pronunciation.areas_for_improvement
                }
            },
            "metrics": {
                "wpm": scorecard.fluency_metrics.words_per_minute,
                "total_words": scorecard.fluency_metrics.total_words,
                "filler_ratio": scorecard.fluency_metrics.filler_frequency_percent,
                "ttr": scorecard.lexical_metrics.type_token_ratio,
                "cefr_distribution": scorecard.lexical_metrics.cefr_distribution,
                "complex_sentence_ratio": scorecard.grammar_metrics.complex_sentence_ratio,
                "intelligibility_score": scorecard.pronunciation_metrics.intelligibility_score
            },
            "sentence_upgrades": [
                {
                    "original": u.original,
                    "upgraded": u.upgraded,
                    "target_band": u.target_band,
                    "rationale": u.linguistic_rationale
                }
                for u in scorecard.sentence_upgrades
            ],
            "action_plan": scorecard.personalized_action_plan
        }
