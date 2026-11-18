"""
Curated IELTS Speaking Question Bank with official Cambridge-standard test sets.
Includes structured Part 1 familiar questions, Part 2 cue cards, and Part 3 abstract discussions.
"""

from typing import List, Optional
from examiner_engine.models import (
    Part1Question,
    Part2CueCard,
    Part3Question,
    IELTSTestSet
)

# Test Set 1: Technology & Society
TEST_SET_1 = IELTSTestSet(
    id="ielts_set_tech_01",
    topic_theme="Technology, Artificial Intelligence & Modern Life",
    part1_topics=["Mobile Phones & Apps", "Online Communication"],
    part1_questions=[
        Part1Question(
            id="p1_tech_01",
            topic="Mobile Phones & Apps",
            question_text="How often do you use mobile apps in your daily life, and what kind of apps do you find most useful?",
            target_duration_seconds=25,
            key_themes=["frequency", "app types", "utility"]
        ),
        Part1Question(
            id="p1_tech_02",
            topic="Mobile Phones & Apps",
            question_text="Do you prefer texting people or calling them? Why?",
            target_duration_seconds=25,
            key_themes=["communication preference", "convenience", "social style"]
        ),
        Part1Question(
            id="p1_tech_03",
            topic="Online Communication",
            question_text="Have you ever felt that you spend too much time on electronic devices?",
            target_duration_seconds=25,
            key_themes=["screen time", "awareness", "habits"]
        ),
        Part1Question(
            id="p1_tech_04",
            topic="Online Communication",
            question_text="What do you think are the advantages of meeting people face-to-face compared to online?",
            target_duration_seconds=30,
            key_themes=["face-to-face interaction", "body language", "interpersonal bonds"]
        )
    ],
    part2_cue_card=Part2CueCard(
        id="p2_tech_01",
        topic="A Technological Product or Software",
        title="Describe a piece of technology or application that has significantly helped you in your work or studies.",
        prompts=[
            "What this technology or application is",
            "When and how you first discovered it",
            "What features or tools it offers that you rely on",
            "And explain why this technology has made such a significant difference to you."
        ],
        round_off_questions=[
            "Do many people you know use this same technology?",
            "Do you think it will still be useful five years from now?"
        ],
        prep_time_seconds=60,
        target_speaking_seconds=120
    ),
    part3_questions=[
        Part3Question(
            id="p3_tech_01",
            theme="Automation and Employment",
            question_text="Some people believe artificial intelligence will replace most white-collar jobs. To what extent do you agree with this view?",
            target_duration_seconds=45,
            sub_probes=[
                "Why do you think certain professions are more resilient to automation than others?",
                "Could this lead to increased socioeconomic inequality?"
            ]
        ),
        Part3Question(
            id="p3_tech_02",
            theme="Digital Literacy and the Elderly",
            question_text="How can governments ensure that older generations are not left behind as societies transition into fully cashless and digital environments?",
            target_duration_seconds=45,
            sub_probes=[
                "Do you think tech companies should bear any moral responsibility for digital accessibility?",
                "Are traditional alternatives, like physical bank branches, still essential?"
            ]
        ),
        Part3Question(
            id="p3_tech_03",
            theme="Privacy and Surveillance",
            question_text="Do you believe people have willingly surrendered too much personal privacy in exchange for the convenience of smart devices?",
            target_duration_seconds=45,
            sub_probes=[
                "Is it possible for an individual to maintain true digital privacy today?",
                "What regulations might be necessary to safeguard personal data?"
            ]
        )
    ]
)

# Test Set 2: Environment, Nature & Sustainability
TEST_SET_2 = IELTSTestSet(
    id="ielts_set_env_02",
    topic_theme="Environment, Nature & Sustainability",
    part1_topics=["Weather & Seasons", "Parks & Green Spaces"],
    part1_questions=[
        Part1Question(
            id="p1_env_01",
            topic="Weather & Seasons",
            question_text="What kind of weather do you enjoy the most, and how does it affect your mood?",
            target_duration_seconds=25,
            key_themes=["weather preference", "mood", "outdoor plans"]
        ),
        Part1Question(
            id="p1_env_02",
            topic="Weather & Seasons",
            question_text="Has the climate in your home region changed noticeably in recent years?",
            target_duration_seconds=25,
            key_themes=["climate shifts", "temperatures", "local observations"]
        ),
        Part1Question(
            id="p1_env_03",
            topic="Parks & Green Spaces",
            question_text="Do you often visit parks or nature reserves in your city?",
            target_duration_seconds=25,
            key_themes=["recreation", "urban parks", "frequency"]
        ),
        Part1Question(
            id="p1_env_04",
            topic="Parks & Green Spaces",
            question_text="Why do you think it is important for modern cities to invest in public green areas?",
            target_duration_seconds=30,
            key_themes=["urban health", "air quality", "mental well-being"]
        )
    ],
    part2_cue_card=Part2CueCard(
        id="p2_env_02",
        topic="An Environmental Initiative",
        title="Describe an environmental initiative, law, or campaign that you have heard about or participated in.",
        prompts=[
            "What the initiative or campaign is about",
            "Where and when it was introduced",
            "What specific actions people or businesses were encouraged to take",
            "And explain how effective you think this initiative has been so far."
        ],
        round_off_questions=[
            "Did this initiative receive broad public support?",
            "Would you be interested in taking part in similar programs in the future?"
        ],
        prep_time_seconds=60,
        target_speaking_seconds=120
    ),
    part3_questions=[
        Part3Question(
            id="p3_env_01",
            theme="Individual vs Corporate Responsibility",
            question_text="Who should bear the primary responsibility for tackling climate change: individual consumers or multinational corporations?",
            target_duration_seconds=45,
            sub_probes=[
                "Why do many people feel their individual lifestyle choices make little difference?",
                "What can governments do to incentivize businesses to adopt greener practices?"
            ]
        ),
        Part3Question(
            id="p3_env_02",
            theme="Economic Growth vs Environmental Protection",
            question_text="Is it realistic for developing nations to prioritize environmental conservation when their primary objective is rapid economic expansion?",
            target_duration_seconds=45,
            sub_probes=[
                "Should industrialized countries offer financial compensation or clean tech to developing nations?",
                "Can sustainable practices actually generate profitable industries?"
            ]
        ),
        Part3Question(
            id="p3_env_03",
            theme="Environmental Education in Schools",
            question_text="How effective is formal environmental education in shaping long-term ecological behavior among young people?",
            target_duration_seconds=45,
            sub_probes=[
                "Do practical activities, like tree planting, have a greater impact than classroom theory?",
                "How do parental habits influence a child's ecological mindset?"
            ]
        )
    ]
)

# Test Set 3: Urban vs Rural Life, Architecture & Heritage
TEST_SET_3 = IELTSTestSet(
    id="ielts_set_urban_03",
    topic_theme="Urbanization, Historic Architecture & Communities",
    part1_topics=["Hometown & Neighborhood", "Accommodation"],
    part1_questions=[
        Part1Question(
            id="p1_urban_01",
            topic="Hometown & Neighborhood",
            question_text="Can you describe the neighborhood where you currently live?",
            target_duration_seconds=25,
            key_themes=["location", "facilities", "community atmosphere"]
        ),
        Part1Question(
            id="p1_urban_02",
            topic="Hometown & Neighborhood",
            question_text="What do you like most about your local area, and what would you improve?",
            target_duration_seconds=30,
            key_themes=["amenities", "traffic", "greenery"]
        ),
        Part1Question(
            id="p1_urban_03",
            topic="Accommodation",
            question_text="Do you live in a house or an apartment, and which do you prefer?",
            target_duration_seconds=25,
            key_themes=["housing type", "comfort", "space"]
        ),
        Part1Question(
            id="p1_urban_04",
            topic="Accommodation",
            question_text="What kind of home would you like to live in in the future?",
            target_duration_seconds=25,
            key_themes=["future plans", "architecture", "ideal living space"]
        )
    ],
    part2_cue_card=Part2CueCard(
        id="p2_urban_03",
        topic="An Impressive Building or Monument",
        title="Describe a historic or architecturally significant building that you have visited or know about.",
        prompts=[
            "Where this building is located",
            "What it looks like and what materials it was built with",
            "What historical or cultural purpose it served",
            "And explain why this building made such a strong impression on you."
        ],
        round_off_questions=[
            "Is this building popular among tourists?",
            "Have you visited it more than once?"
        ],
        prep_time_seconds=60,
        target_speaking_seconds=120
    ),
    part3_questions=[
        Part3Question(
            id="p3_urban_01",
            theme="Historic Preservation vs Modern Development",
            question_text="Should municipal governments spend substantial public funds maintaining old historic buildings, or should those spaces be redeveloped for modern housing?",
            target_duration_seconds=45,
            sub_probes=[
                "How do historical monuments contribute to a city's cultural identity?",
                "Is it possible to blend ancient architecture with high-density modern skyscrapers?"
            ]
        ),
        Part3Question(
            id="p3_urban_02",
            theme="Urban Congestion and Infrastructure",
            question_text="What are the biggest challenges faced by mega-cities today regarding transportation and housing?",
            target_duration_seconds=45,
            sub_probes=[
                "Will satellite towns and decentralized remote working ease urban overcrowding?",
                "How does poor public transit impact social mobility?"
            ]
        ),
        Part3Question(
            id="p3_urban_03",
            theme="Sense of Community in Modern Cities",
            question_text="Why do many residents in large modern cities feel socially isolated despite living in densely populated neighborhoods?",
            target_duration_seconds=45,
            sub_probes=[
                "How can urban planners design public spaces that foster interpersonal interaction?",
                "Do suburban or rural communities naturally have stronger social safety nets?"
            ]
        )
    ]
)

ALL_TEST_SETS: List[IELTSTestSet] = [TEST_SET_1, TEST_SET_2, TEST_SET_3]


def get_test_set_by_id(test_id: str) -> Optional[IELTSTestSet]:
    """Retrieve an IELTS test set by its unique ID."""
    for ts in ALL_TEST_SETS:
        if ts.id == test_id:
            return ts
    return None


def get_all_test_sets() -> List[IELTSTestSet]:
    """Retrieve all available test sets in the question bank."""
    return ALL_TEST_SETS
