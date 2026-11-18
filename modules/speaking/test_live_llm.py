"""
Interactive CLI Tester for Live Frontier LLM Evaluation (Gemini 1.5 Pro / GPT-4o).
Tests API key connection, sends sample IELTS candidate speech, and displays live evaluator results.
"""

import sys
import os
import time
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scoring_engine.llm_evaluator import MultiAgentLLMEvaluator
from scoring_engine.scoring_pipeline import IELTSScoringPipeline
from scoring_engine.report_generator import ReportGenerator


SAMPLE_CANDIDATE_TURNS = [
    {
        "speaker": "CANDIDATE",
        "stage": "PART1_QUESTIONS",
        "text": "Well, I use mobile applications constantly throughout the day, especially productivity tools like calendar apps and language platforms. They help me manage my daily routine and stay organized.",
        "duration_seconds": 22.0
    },
    {
        "speaker": "CANDIDATE",
        "stage": "PART2_SPEAKING",
        "text": "I would like to talk about Notion, an application that significantly enhanced my academic productivity. I first discovered it during my final undergraduate semester when balancing multiple dissertations was overwhelming. It provided a modular database system allowing me to organize notes, citations, and daily deadlines seamlessly.",
        "duration_seconds": 65.0
    },
    {
        "speaker": "CANDIDATE",
        "stage": "PART3_DISCUSSION",
        "text": "I think artificial intelligence will automate repetitive analytical tasks, such as basic data entry. However, roles requiring emotional intelligence and critical ethical judgment will likely remain predominantly human.",
        "duration_seconds": 38.0
    }
]


def print_banner(title: str, char: str = "="):
    line = char * 68
    print(f"\n{line}\n {title}\n{line}")


def main():
    parser = argparse.ArgumentParser(description="Test Live Frontier LLM IELTS Evaluator")
    parser.add_argument("--provider", choices=["gemini", "openai"], default="gemini", help="LLM Provider (default: gemini)")
    parser.add_argument("--key", type=str, default="", help="API Key (or reads from .env / environment)")
    parser.add_argument("--model", type=str, default="", help="Model name (e.g. gemini-1.5-pro, gpt-4o)")
    args = parser.parse_args()

    print_banner("LIVE FRONTIER LLM EVALUATOR TEST SUITE", "=")

    provider = args.provider.lower()
    default_model = "gemini-1.5-pro" if provider == "gemini" else "gpt-4o"
    target_model = args.model or os.environ.get(f"{provider.upper()}_MODEL", default_model)

    # Resolve API Key
    api_key = args.key or os.environ.get(f"{provider.upper()}_API_KEY", "")

    if not api_key:
        env_var_name = f"{provider.upper()}_API_KEY"
        print(f"No {env_var_name} detected in environment or .env file.")
        print(f"You can get a free Gemini API key at: https://aistudio.google.com/app/apikey\n")
        api_key = input(f"Enter your {provider.upper()} API Key (or press Enter to test local fallback): ").strip()

        if api_key:
            save_choice = input("Would you like to save this key to .env for the app? [y/N]: ").strip().lower()
            if save_choice == "y":
                MultiAgentLLMEvaluator.save_api_key_to_env(provider, api_key, target_model)
                print(f"Saved {env_var_name} to .env file.")

    if api_key:
        os.environ[f"{provider.upper()}_API_KEY"] = api_key
        os.environ[f"{provider.upper()}_MODEL"] = target_model

        # 1. Test live ping connection
        print(f"\nPinging {provider.upper()} ({target_model})...")
        ping_res = MultiAgentLLMEvaluator.test_live_connection(provider, api_key, target_model)

        if ping_res.get("success"):
            print(f"[SUCCESS] Live connection verified! Latency: {ping_res.get('latency_ms')}ms")
            print(f"Response: {ping_res.get('reply')}")
        else:
            print(f"[ERROR] Connection failed: {ping_res.get('error')}")
            return
    else:
        print("\nProceeding with calibrated deterministic local evaluator...")

    # 2. Run full evaluation on candidate turns
    print_banner(f"RUNNING LIVE EVALUATION ON CANDIDATE SPEECH ({target_model if api_key else 'Local Arbitrator'})", "-")

    mock_payload = {
        "session_id": "live_llm_test_session_01",
        "candidate_name": "Maria Silva",
        "test_theme": "Technology & Artificial Intelligence",
        "transcript": SAMPLE_CANDIDATE_TURNS
    }

    t0 = time.time()
    scorecard = IELTSScoringPipeline.evaluate_session(mock_payload, use_llm=True)
    duration = round(time.time() - t0, 2)

    # 3. Display Results
    print(f"\nEvaluation completed in {duration}s!")
    print(f"\nOVERALL BAND SCORE: {scorecard.overall_band} / 9.0\n")

    print(f"CRITERIA BREAKDOWN:")
    print(f"  • Fluency & Coherence (FC) : Band {scorecard.fluency_and_coherence.band:.1f}")
    print(f"    - Summary: {scorecard.fluency_and_coherence.descriptor_summary}")
    if scorecard.fluency_and_coherence.cited_evidence:
        print(f"    - Cited Evidence: {', '.join(scorecard.fluency_and_coherence.cited_evidence[:2])}")

    print(f"\n  • Lexical Resource (LR)    : Band {scorecard.lexical_resource.band:.1f}")
    print(f"    - Summary: {scorecard.lexical_resource.descriptor_summary}")
    if scorecard.lexical_resource.cited_evidence:
        print(f"    - Cited Evidence: {', '.join(scorecard.lexical_resource.cited_evidence[:2])}")

    print(f"\n  • Grammatical Range (GRA)  : Band {scorecard.grammatical_range_and_accuracy.band:.1f}")
    print(f"    - Summary: {scorecard.grammatical_range_and_accuracy.descriptor_summary}")

    print(f"\n  • Pronunciation (PR)       : Band {scorecard.pronunciation.band:.1f}")
    print(f"    - Summary: {scorecard.pronunciation.descriptor_summary}")

    print_banner("BAND 8.5+ SENTENCE UPGRADES (GENERATED BY LLM)", "-")
    for idx, u in enumerate(scorecard.sentence_upgrades, 1):
        print(f"Example {idx} (Target: Band {u.target_band}):")
        print(f"  Original: \"{u.original}\"")
        print(f"  Upgraded: \"{u.upgraded}\"")
        print(f"  Why:      {u.linguistic_rationale}\n")

    print_banner("PERSONALIZED ACTION PLAN", "-")
    for idx, step in enumerate(scorecard.personalized_action_plan, 1):
        print(f"  [{idx}] {step}")

    print_banner("TEST COMPLETE", "=")


if __name__ == "__main__":
    main()
