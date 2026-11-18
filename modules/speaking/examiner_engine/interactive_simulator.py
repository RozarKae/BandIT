"""
Interactive CLI Simulator for IELTS Speaking Practice.
Demonstrates the full examiner persona, timing controls, and state transitions.
"""

import sys
import os
import time
import json

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from examiner_engine.models import ExamStage
from examiner_engine.question_bank import ALL_TEST_SETS
from examiner_engine.state_machine import IELTSExaminerSession


def print_banner(text: str, char: str = "="):
    line = char * 68
    print(f"\n{line}\n {text}\n{line}")


def run_interactive_simulation():
    print_banner("OFFICIAL IELTS SPEAKING SIMULATOR (AI EXAMINER)", "=")
    print("Select a test topic:")
    for idx, ts in enumerate(ALL_TEST_SETS, 1):
        print(f" [{idx}] {ts.topic_theme}")
    
    choice = input("\nEnter choice (1-3) [default: 1]: ").strip()
    idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(ALL_TEST_SETS) else 0
    selected_set = ALL_TEST_SETS[idx]

    candidate_name = input("Enter candidate name [default: Alex]: ").strip() or "Alex"
    session = IELTSExaminerSession(test_set=selected_set, candidate_name=candidate_name)

    print_banner(f"TEST SESSION STARTED: {selected_set.topic_theme}", "-")
    
    # 1. Start exam
    action = session.start_exam()
    print(f"\n[EXAMINER]: {action.utterance}\n")

    while action.stage != ExamStage.COMPLETED:
        if action.stage == ExamStage.PART2_PREPARATION:
            cue = action.display_cue_card
            print_banner(f"PART 2: CUE CARD - {cue['title']}", "*")
            print("You have 1 minute to prepare notes. You should say:")
            for p in cue["prompts"]:
                print(f"  • {p}")
            print("\n[Timer]: 60 seconds preparation timer started.")
            print("(Press Enter to finish preparation and start speaking immediately...)")
            
            # Simple skip or wait
            input("> ")
            print("[Timer]: Preparation finished.")
            action = session.trigger_part2_prep_finished()
            print(f"\n[EXAMINER]: {action.utterance}\n")
            continue

        if action.context_note:
            print(f"*(System Note: {action.context_note})*")

        # Candidate response turn
        start_time = time.time()
        print(f"[{candidate_name} (Speak / Type response)]:")
        candidate_input = input("> ").strip()
        elapsed_seconds = max(round(time.time() - start_time, 1), 12.0)  # Default minimum simulated speech

        if not candidate_input:
            candidate_input = "I believe this is an important area with significant long-term effects."

        action = session.handle_candidate_response(candidate_input, duration_seconds=elapsed_seconds)
        print(f"\n[EXAMINER]: {action.utterance}\n")

    print_banner("EXAM CONCLUDED - GENERATING SCORING PAYLOAD", "=")
    payload = session.export_session_payload()
    
    output_path = os.path.join(os.path.dirname(__file__), "sample_session_transcript.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Session transcript saved to: {output_path}")
    print(f"Total dialogue turns: {payload['total_turns']}")
    print("Ready to be processed by the Scoring and Rubric Calibration Engine.")


if __name__ == "__main__":
    run_interactive_simulation()
