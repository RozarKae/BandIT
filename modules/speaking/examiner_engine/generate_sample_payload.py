"""
Generate a realistic sample candidate session transcript for testing the Scoring Engine.
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from examiner_engine.question_bank import TEST_SET_1
from examiner_engine.state_machine import IELTSExaminerSession


def generate_sample_transcript():
    session = IELTSExaminerSession(test_set=TEST_SET_1, candidate_name="Maria Silva")

    # 1. Greeting
    session.start_exam()
    session.handle_candidate_response(
        "Good afternoon. My name is Maria Silva, and you can simply call me Maria.",
        duration_seconds=5.2
    )

    # 2. Part 1 Questions
    # Q1: Mobile apps
    session.handle_candidate_response(
        "Well, I use mobile applications constantly throughout the day, especially productivity tools like calendar apps and language learning platforms. They help me manage my daily routine and stay organized.",
        duration_seconds=22.4
    )
    # Q2: Texting vs calling
    session.handle_candidate_response(
        "To be honest, it really depends on the situation. For quick logistical updates or casual chats, I prefer texting because it is convenient and non-intrusive. However, for complex discussions or when I miss my family, phone calls are much more personal.",
        duration_seconds=26.1
    )
    # Q3: Too much time on devices
    session.handle_candidate_response(
        "Yes, definitely. Occasionally I find myself mindlessly scrolling through social media feeds for hours, especially late in the evening. I have recently tried setting daily screen time limits to curb this habit.",
        duration_seconds=24.5
    )
    # Q4: Face-to-face vs online
    session.handle_candidate_response(
        "I think in-person interaction provides subtle non-verbal cues, such as eye contact and body language, which are often lost through digital screens. It builds genuine rapport and deeper emotional connections.",
        duration_seconds=28.3
    )

    # 3. Part 2 Cue Card
    session.trigger_part2_prep_finished()
    # Monologue (~68 seconds, 134 words = ~118 WPM)
    monologue = (
        "I would like to talk about a project management tool called Notion, which has significantly enhanced my academic productivity. "
        "I first encountered this software about two years ago during my final undergraduate semester when I was juggling multiple dissertations and coursework deadlines. "
        "Before using it, my notes were scattered across various physical notebooks and digital sticky notes, which was quite chaotic. "
        "Notion allowed me to create customizable databases, track research progress with Kanban boards, and embed academic citations seamlessly. "
        "What makes it indispensable for me is its versatility; whether I need a simple daily checklist or an elaborate literature review matrix, "
        "it adapts to my needs. It ultimately saved me countless hours of stress and made my study sessions far more structured."
    )
    session.handle_candidate_response(monologue, duration_seconds=68.0)

    # Round-off questions
    session.handle_candidate_response(
        "Yes, quite a few of my colleagues and fellow students have adopted it recently.",
        duration_seconds=6.8
    )
    session.handle_candidate_response(
        "Without doubt, although with rapid advancements in AI features, it will probably look quite different in five years.",
        duration_seconds=11.2
    )

    # 4. Part 3 Discussion
    # Q1: AI replacing white-collar jobs
    session.handle_candidate_response(
        "I think artificial intelligence will automate repetitive analytical tasks, such as basic data entry or contract review. However, roles requiring emotional intelligence, critical ethical judgment, and complex negotiation will likely remain predominantly human. Therefore, it will transform job roles rather than eliminate employment entirely.",
        duration_seconds=42.0
    )

    # Q2: Elderly digital literacy (brief answer to test dynamic probe trigger)
    session.handle_candidate_response(
        "Governments should establish free digital workshops in local community centers.",
        duration_seconds=6.5
    )
    # Candidate response to examiner probe
    session.handle_candidate_response(
        "Because many senior citizens feel intimidated by touchscreen technology and banking applications, so patient, step-by-step human tutoring in community hubs is essential to prevent digital exclusion.",
        duration_seconds=26.4
    )

    # Q3: Privacy vs convenience
    session.handle_candidate_response(
        "Regrettably, modern consumers often sacrifice privacy for immediate convenience. Clicking 'agree' on algorithmic terms of service is vastly easier than scrutinizing data protection agreements, but it exposes personal behavioral profiles to commercial exploitation.",
        duration_seconds=39.5
    )

    payload = session.export_session_payload()
    output_file = os.path.join(os.path.dirname(__file__), "sample_session_transcript.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Sample transcript generated at: {output_file}")
    print(f"Total turns: {payload['total_turns']}")


if __name__ == "__main__":
    generate_sample_transcript()
