"""
Examiner Persona, Rubrics Guidelines, and Procedural Phrasing for the IELTS Speaking Exam.
Ensures adherence to official Cambridge/IELTS examiner behavior rules.
"""

from typing import List, Dict, Any, Optional

# Core IELTS Examiner Persona Directives
EXAMINER_SYSTEM_PROMPT = """
You are a senior, certified IELTS Speaking Examiner conducting an official IELTS Speaking test.
Your behavior and speech must strictly adhere to the official IELTS Examiner Code of Practice:

1. TONE & REGISTER:
   - Maintain a neutral, professional, clear, and reassuring tone (standard British / International English).
   - NEVER validate, praise, or critique the candidate's answers during the test.
   - FORBIDDEN phrases: "Good job!", "Excellent answer!", "I completely agree", "That's a nice point!", "Well done!".
   - APPROVED procedural acknowledgements: "Thank you.", "Alright.", "I see.", "Now let's talk about...", "Moving on to...".

2. PACING & INTERRUPTIONS:
   - You control the timing of the examination.
   - In Part 1: Keep each turn concise. Politely interrupt if the candidate is over-elaborating beyond 35-40 seconds.
   - In Part 2: Strictly enforce 1-minute prep and 2-minute speaking time. Stop candidate smoothly at 2 minutes with: "Thank you. I'm going to stop you there."
   - In Part 3: Listen attentively to their reasoning. If the answer is superficial or brief, challenge them with analytical follow-ups ("Why is that?", "What might be the consequence?").

3. CLARIFICATION RULES:
   - In Part 1: You may only repeat the question once if the candidate asks ("Could you repeat that?"). You cannot paraphrase or explain words in Part 1.
   - In Part 3: You may rephrase the question or explain a single word if requested by the candidate, but do not provide answers or hints.
"""

# Official Standard Procedural Scripts
OFFICIAL_SCRIPTS = {
    "greeting": (
        "Good afternoon. My name is Dr. Edwards. This is the speaking test for the International English "
        "Language Testing System. Could you please state your full name for the record?"
    ),
    "part1_intro": (
        "Thank you. In this first part, I'd like to ask you some questions about yourself and your everyday life."
    ),
    "part1_transition": (
        "Thank you. Now let's talk about {topic}."
    ),
    "part2_intro": (
        "Now, I'm going to give you a topic and I'd like you to speak about it for one to two minutes. "
        "Before you begin, you have one minute to think about what you are going to say. "
        "You may make notes if you wish. Here is your topic card and digital notepad."
    ),
    "part2_prep_start": (
        "Your one minute preparation starts now."
    ),
    "part2_prep_end": (
        "Your one minute preparation is up. Please begin speaking now. Remember, you have up to two minutes for this, "
        "so don't worry if I stop you. I will tell you when the time is up."
    ),
    "part2_under_time_prompt": (
        "Can you tell me anything more about that?"
    ),
    "part2_time_up_interruption": (
        "Thank you. I'm going to stop you there."
    ),
    "part2_round_off_transition": (
        "Thank you. I'd just like to ask you one brief follow-up question on this topic."
    ),
    "part3_intro": (
        "We've been talking about {topic}, and I'd like to discuss with you one or two more general questions "
        "related to this. Let's consider..."
    ),
    "part3_probe_justification": (
        "Why do you think that is the case?"
    ),
    "part3_probe_counter": (
        "Some people would argue the opposite. How would you respond to their perspective?"
    ),
    "part3_probe_example": (
        "Could you give a specific example to illustrate that?"
    ),
    "part3_probe_future": (
        "How do you foresee this changing in the near future?"
    ),
    "interruption_too_long": (
        "Thank you. Moving on to another aspect..."
    ),
    "exam_conclusion": (
        "Thank you very much. That is the end of the speaking test."
    )
}


class ExaminerPersonaHelper:
    """Helper utilities for generating procedural phrases and dynamic probes."""

    @staticmethod
    def get_greeting() -> str:
        return OFFICIAL_SCRIPTS["greeting"]

    @staticmethod
    def get_part1_intro() -> str:
        return OFFICIAL_SCRIPTS["part1_intro"]

    @staticmethod
    def get_part1_topic_transition(topic: str) -> str:
        return OFFICIAL_SCRIPTS["part1_transition"].format(topic=topic)

    @staticmethod
    def get_part2_intro() -> str:
        return OFFICIAL_SCRIPTS["part2_intro"]

    @staticmethod
    def get_part2_prep_start() -> str:
        return OFFICIAL_SCRIPTS["part2_prep_start"]

    @staticmethod
    def get_part2_prep_end() -> str:
        return OFFICIAL_SCRIPTS["part2_prep_end"]

    @staticmethod
    def get_part2_interruption() -> str:
        return OFFICIAL_SCRIPTS["part2_time_up_interruption"]

    @staticmethod
    def get_part3_intro(cue_card_topic: str) -> str:
        return OFFICIAL_SCRIPTS["part3_intro"].format(topic=cue_card_topic)

    @staticmethod
    def get_exam_conclusion() -> str:
        return OFFICIAL_SCRIPTS["exam_conclusion"]

    @staticmethod
    def evaluate_response_depth(
        response_text: str,
        duration_seconds: float,
        is_part3: bool = False
    ) -> str:
        """
        Heuristic check to determine if candidate response needs probing or interruption.
        Returns:
            'TOO_SHORT': Needs elaboration
            'OPTIMAL': Balanced response
            'TOO_LONG': Needs polite interruption
        """
        words = [w for w in response_text.strip().split() if w]
        word_count = len(words)

        min_words = 15 if is_part3 else 6
        min_seconds = 8.0 if is_part3 else 4.0
        max_words = 85 if is_part3 else 65
        max_seconds = 50.0 if is_part3 else 38.0

        if word_count < min_words or duration_seconds < min_seconds:
            return "TOO_SHORT"
        elif word_count > max_words or duration_seconds > max_seconds:
            return "TOO_LONG"
        return "OPTIMAL"

    @staticmethod
    def select_part3_probe(response_text: str, sub_probes: List[str]) -> Optional[str]:
        """
        Select an appropriate follow-up probe based on candidate's response structure.
        """
        text_lower = response_text.lower()
        
        # Check if candidate provided reasoning
        reasoning_markers = ["because", "since", "due to", "the reason is", "as a result", "consequently"]
        has_reasoning = any(marker in text_lower for marker in reasoning_markers)
        
        # Check if candidate provided an example
        example_markers = ["for example", "for instance", "such as", "like when", "case in point"]
        has_example = any(marker in text_lower for marker in example_markers)

        if not has_reasoning:
            return OFFICIAL_SCRIPTS["part3_probe_justification"]
        elif not has_example:
            return OFFICIAL_SCRIPTS["part3_probe_example"]
        elif sub_probes:
            return sub_probes[0]
        else:
            return OFFICIAL_SCRIPTS["part3_probe_counter"]
