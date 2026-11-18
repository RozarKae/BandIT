# BandIT - Band IELTS Test Platform

**BandIT** is an end-to-end, multi-module AI-powered IELTS preparation and scoring platform covering all four official skills:
1. 🗣️ **Speaking**: Real-time AI examiner simulation (Parts 1, 2, and 3), cue card timers, live audio transcription, acoustic rhythm/pause analytics, and frontier LLM (Gemini 1.5 Pro / GPT-4o) scoring.
2. ✍️ **Writing**: Task 1 (Academic report / General letter) and Task 2 (Discursive essay) evaluation across Task Response (TR), Coherence & Cohesion (CC), Lexical Resource (LR), and Grammatical Range & Accuracy (GRA).
3. 📖 **Reading**: 3 Academic/General passages, 40-question automated scoring engine, and raw-to-band conversion tables.
4. 🎧 **Listening**: 4 recorded sections, 40 questions, diverse international accents (British, Australian, North American), and spelling strictness checks.

---

## Multi-Module Monorepo Architecture

```
d:\BandIT\
├── modules\
│   ├── speaking\                # Speaking Module (Examiner Persona, ASR, LLM Evaluator)
│   │   ├── examiner_engine\     # Turn-taking state machine & Cambridge question bank
│   │   ├── scoring_engine\      # 4-criterion scorer (FC, LR, GRA, PR), GoP acoustic analysis
│   │   ├── api_server.py        # Speaking REST API server
│   │   ├── test_live_llm.py     # Live LLM examiner CLI tester
│   │   └── tests\               # Comprehensive unit test suites
│   │
│   ├── writing\                 # Writing Module
│   │   └── writing_evaluator.py # Task 1 & Task 2 scoring, word count check, weighted band formula
│   │
│   ├── reading\                 # Reading Module
│   │   └── reading_engine.py    # 40-question raw to band conversion & passage schemas
│   │
│   └── listening\               # Listening Module
│       └── listening_engine.py  # 4-section player, spelling sensitivity & raw to band map
│
├── shared\                      # Shared IELTS Core Logic
│   └── band_calculator.py       # Official 4-module overall band calculator (L, R, W, S) & CEFR levels
│
├── apps\
│   ├── web\                     # Next.js 16 + React 19 + TailwindCSS Portal
│   │   ├── app\
│   │   │   ├── components\      # AudioWaveform, CueCardModal, ScorecardView, SettingsModal
│   │   │   └── page.tsx         # Unified 4-module dashboard & practice room
│   │   └── package.json
│   │
│   └── api-gateway\             # Unified Multi-Module API Gateway
│
├── .gitignore
└── README.md
```

---

## Official Overall Band Scoring Rule

BandIT enforces the official Cambridge IELTS rounding standard across all four modules:

$$\text{Overall Band} = \text{round\_to\_half}\left(\frac{\text{Listening} + \text{Reading} + \text{Writing} + \text{Speaking}}{4}\right)$$

- If the average ends in `.25`, it rounds up to `.5` (e.g., $6.25 \to 6.5$).
- If the average ends in `.75`, it rounds up to the next integer band (e.g., $6.75 \to 7.0$).
- If the fractional part is $< .25$, it rounds down to the whole band.
- If the fractional part is $\ge .25$ and $< .75$, it rounds to the half band.

---

## Quick Start

### 1. Launch the Speaking & Scoring Backend API
```powershell
cd d:\BandIT\modules\speaking
$env:PYTHONPATH = "d:\BandIT\modules\speaking"
python api_server.py 8000
```

### 2. Launch the Web Portal
```powershell
cd d:\BandIT\apps\web
npm install
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## Git Repository
Initialized as a clean git repository in `d:\BandIT`.
