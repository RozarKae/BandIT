"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  Award,
  Sparkles,
  HelpCircle,
  PlayCircle,
  User,
  Radio,
  FileCheck2,
} from "lucide-react";
import AudioWaveform from "./components/AudioWaveform";
import CueCardModal from "./components/CueCardModal";
import ScorecardView from "./components/ScorecardView";
import SettingsModal from "./components/SettingsModal";
import { Settings, PenTool, BookOpen, Headphones, MessageSquare, Layers, CheckCircle2 } from "lucide-react";

interface Topic {
  id: string;
  theme: string;
  part1_topics: string[];
  part2_cue_card_title: string;
}

interface ExaminerActionData {
  stage: string;
  utterance: string;
  requires_candidate_input: boolean;
  input_timeout_seconds: number | null;
  display_cue_card?: {
    id: string;
    title: string;
    prompts: string[];
    prep_time_seconds: number;
    target_speaking_seconds: number;
  };
  timer_countdown_seconds?: number;
  context_note?: string;
}

const DEFAULT_TOPICS: Topic[] = [
  {
    id: "ielts_set_tech_01",
    theme: "Technology, Artificial Intelligence & Modern Life",
    part1_topics: ["Mobile Phones & Apps", "Online Communication"],
    part2_cue_card_title: "Describe a piece of technology or application that has significantly helped you.",
  },
  {
    id: "ielts_set_env_02",
    theme: "Environment, Nature & Sustainability",
    part1_topics: ["Weather & Seasons", "Parks & Green Spaces"],
    part2_cue_card_title: "Describe an environmental initiative, law, or campaign you know about.",
  },
  {
    id: "ielts_set_urban_03",
    theme: "Urbanization, Historic Architecture & Communities",
    part1_topics: ["Hometown & Neighborhood", "Accommodation"],
    part2_cue_card_title: "Describe a historic or architecturally significant building.",
  },
];

const API_BASE = "http://127.0.0.1:8000";

export default function IELTSPracticeApp() {
  // App view modes
  const [viewState, setViewState] = useState<"SETUP" | "INTERVIEW" | "SCORECARD">("SETUP");
  const [activeModule, setActiveModule] = useState<"speaking" | "writing" | "reading" | "listening">("speaking");

  // Setup state
  const [topics, setTopics] = useState<Topic[]>(DEFAULT_TOPICS);
  const [selectedTopicId, setSelectedTopicId] = useState<string>("ielts_set_tech_01");
  const [candidateName, setCandidateName] = useState<string>("Alex");
  const [targetBand, setTargetBand] = useState<string>("7.5");

  // Interview state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentAction, setCurrentAction] = useState<ExaminerActionData | null>(null);
  const [showCueCard, setShowCueCard] = useState<boolean>(false);
  const [ttsEnabled, setTtsEnabled] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Audio & Candidate recording state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingDuration, setRecordingDuration] = useState<number>(0);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const [candidateText, setCandidateText] = useState<string>("");
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);
  const durationTimerRef = useRef<NodeJS.Timeout | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Scorecard state
  const [scorecardData, setScorecardData] = useState<any | null>(null);
  const [markdownReport, setMarkdownReport] = useState<string>("");
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Load available topics on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/topics`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.topics) setTopics(data.topics);
      })
      .catch((err) => {
        console.warn("Using fallback local topics:", err);
      });
  }, []);

  // Text-to-Speech (TTS) for Examiner Utterance
  const speakExaminerUtterance = (text: string) => {
    if (!ttsEnabled || typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    
    // Select British English voice if available
    const voices = window.speechSynthesis.getVoices();
    const britishVoice = voices.find((v) => v.lang === "en-GB" || v.name.includes("British") || v.name.includes("UK"));
    if (britishVoice) utterance.voice = britishVoice;

    window.speechSynthesis.speak(utterance);
  };

  // Start new mock test
  const handleStartExam = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/sessions/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          test_set_id: selectedTopicId,
          candidate_name: candidateName || "Candidate",
        }),
      });
      const data = await res.json();
      setSessionId(data.session_id);
      setCurrentAction(data.action);
      setViewState("INTERVIEW");
      speakExaminerUtterance(data.action.utterance);
    } catch (err) {
      console.error("Failed to start session:", err);
      alert("Please ensure the Python API server is running on http://127.0.0.1:8000");
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle microphone recording
  const handleToggleRecording = async () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      if (durationTimerRef.current) clearInterval(durationTimerRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (audioStream) {
        audioStream.getTracks().forEach((track) => track.stop());
        setAudioStream(null);
      }
    } else {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setAudioStream(stream);
        setIsRecording(true);
        setRecordingDuration(0);

        // Start media recorder
        let mimeType = "audio/webm";
        if (!MediaRecorder.isTypeSupported("audio/webm")) {
          mimeType = "audio/mp4";
        }
        const mediaRecorder = new MediaRecorder(stream, { mimeType });
        audioChunksRef.current = [];
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
          if (audioBlob.size > 0) {
            setIsTranscribing(true);
            const reader = new FileReader();
            reader.onloadend = async () => {
              const base64Audio = reader.result as string;
              try {
                const res = await fetch(`${API_BASE}/api/audio/transcribe`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    audio_base64: base64Audio,
                    mime_type: mimeType,
                    client_hint: candidateText
                  }),
                });
                const data = await res.json();
                if (data.transcript) {
                  setCandidateText(data.transcript);
                }
              } catch (e) {
                console.warn("Audio transcription error, keeping existing text:", e);
              } finally {
                setIsTranscribing(false);
              }
            };
            reader.readAsDataURL(audioBlob);
          }
        };

        mediaRecorder.start(250);
        mediaRecorderRef.current = mediaRecorder;

        durationTimerRef.current = setInterval(() => {
          setRecordingDuration((prev) => prev + 1);
        }, 1000);

        // Client-side Web Speech recognition for instant visual feedback
        const SpeechRecognition =
          (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRecognition) {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = "en-US";

          recognition.onresult = (event: any) => {
            let transcript = "";
            for (let i = 0; i < event.results.length; i++) {
              transcript += event.results[i][0].transcript + " ";
            }
            if (transcript.trim()) {
              setCandidateText(transcript.trim());
            }
          };

          recognition.start();
        }
      } catch (err) {
        console.warn("Microphone access unavailable or denied. You can type your response:", err);
        setIsRecording(true);
        durationTimerRef.current = setInterval(() => {
          setRecordingDuration((prev) => prev + 1);
        }, 1000);
      }
    }
  };

  // Submit Spoken Answer to Examiner
  const handleSubmitResponse = async () => {
    if (!sessionId || !candidateText.trim()) return;

    if (isRecording) {
      setIsRecording(false);
      if (durationTimerRef.current) clearInterval(durationTimerRef.current);
      if (audioStream) {
        audioStream.getTracks().forEach((t) => t.stop());
        setAudioStream(null);
      }
    }

    setIsLoading(true);
    const duration = Math.max(recordingDuration, 15);

    try {
      const res = await fetch(`${API_BASE}/api/sessions/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          candidate_text: candidateText,
          duration_seconds: duration,
        }),
      });

      const data = await res.json();
      setCurrentAction(data.action);
      setCandidateText("");
      setRecordingDuration(0);

      // Check if Part 2 preparation started
      if (data.action.stage === "PART2_PREPARATION" && data.action.display_cue_card) {
        setShowCueCard(true);
      }

      speakExaminerUtterance(data.action.utterance);
    } catch (err) {
      console.error("Failed to advance examiner turn:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Complete Cue Card preparation
  const handleCueCardPrepComplete = async () => {
    setShowCueCard(false);
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/sessions/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          is_prep_finished: true,
        }),
      });
      const data = await res.json();
      setCurrentAction(data.action);
      speakExaminerUtterance(data.action.utterance);
    } catch (err) {
      console.error("Failed to trigger prep complete:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Finish exam and generate full scorecard
  const handleScoreExam = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/sessions/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await res.json();
      if (data.scorecard) {
        setScorecardData(data.scorecard);
        setMarkdownReport(data.markdown_report);
        setViewState("SCORECARD");
      } else {
        alert(data.error || "Unable to score session yet. Answer at least one question.");
      }
    } catch (err) {
      console.error("Failed to score exam:", err);
      alert("Error scoring session.");
    } finally {
      setIsLoading(false);
    }
  };

  const getStageLabel = (stage: string) => {
    switch (stage) {
      case "PART1_ID_CHECK":
        return "Part 1: Verification";
      case "PART1_QUESTIONS":
        return "Part 1: Everyday Topics";
      case "PART2_CUE_CARD_PRESENTED":
      case "PART2_PREPARATION":
        return "Part 2: Cue Card Prep";
      case "PART2_SPEAKING":
        return "Part 2: Long Turn (Monologue)";
      case "PART2_ROUND_OFF":
        return "Part 2: Round-Off";
      case "PART3_DISCUSSION":
        return "Part 3: In-Depth Discussion";
      case "COMPLETED":
        return "Exam Completed";
      default:
        return stage;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-emerald-500 text-white font-black text-xl shadow-lg shadow-blue-500/25 tracking-wider">
              B
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black text-white leading-none tracking-tight">BandIT</h1>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                  Band IELTS Test
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">Official 4-Module AI Assessment Platform</p>
            </div>
          </div>

          {/* Module Switcher Tabs */}
          <div className="flex items-center bg-slate-950/80 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveModule("speaking")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeModule === "speaking"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Speaking</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </button>

            <button
              onClick={() => setActiveModule("writing")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeModule === "writing"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <PenTool className="w-3.5 h-3.5" />
              <span>Writing</span>
            </button>

            <button
              onClick={() => setActiveModule("reading")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeModule === "reading"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Reading</span>
            </button>

            <button
              onClick={() => setActiveModule("listening")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeModule === "listening"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Headphones className="w-3.5 h-3.5" />
              <span>Listening</span>
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 transition-all cursor-pointer shadow-sm"
            >
              <Settings className="w-3.5 h-3.5 text-blue-400" />
              <span>AI Model & Keys</span>
            </button>
            {activeModule === "speaking" && (
              <button
                onClick={() => setTtsEnabled(!ttsEnabled)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
                  ttsEnabled
                    ? "bg-blue-950/60 border-blue-700/50 text-blue-300"
                    : "bg-slate-900 border-slate-700 text-slate-500"
                }`}
              >
                <Volume2 className="w-3.5 h-3.5" />
                <span>Voice: {ttsEnabled ? "ON" : "OFF"}</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 flex flex-col justify-center">
        {/* MODULE 1: SPEAKING (ACTIVE INTERACTIVE SIMULATOR) */}
        {activeModule === "speaking" && (
          <>
            {/* VIEW 1: SETUP & TOPIC SELECTION */}
            {viewState === "SETUP" && (
              <div className="max-w-3xl mx-auto w-full space-y-8 animate-in fade-in duration-300">
                <div className="text-center space-y-2">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-950/60 border border-blue-800/50 text-blue-300">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    Cambridge Standard Simulation
                  </div>
                  <h2 className="text-3xl font-extrabold text-white">Choose Your Speaking Test Topic</h2>
                  <p className="text-sm text-slate-400 max-w-md mx-auto">
                    Practice official IELTS Parts 1, 2, and 3 with turn-taking and examiner feedback.
                  </p>
                </div>

                {/* Candidate Configuration */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1.5">
                        Candidate Full Name
                      </label>
                      <div className="relative">
                        <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                        <input
                          type="text"
                          value={candidateName}
                          onChange={(e) => setCandidateName(e.target.value)}
                          placeholder="e.g. Alex Chen"
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1.5">
                        Target Band Score
                      </label>
                      <select
                        value={targetBand}
                        onChange={(e) => setTargetBand(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer"
                      >
                        <option value="6.5">Band 6.5 (Competent User)</option>
                        <option value="7.0">Band 7.0 (Good User)</option>
                        <option value="7.5">Band 7.5 (Very Good User)</option>
                        <option value="8.0">Band 8.0+ (Superior User)</option>
                      </select>
                    </div>
                  </div>

                  {/* Topic Selector */}
                  <div>
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2.5">
                      Select Official Question Set
                    </label>
                    <div className="grid grid-cols-1 gap-3">
                      {topics.map((t) => (
                        <div
                          key={t.id}
                          onClick={() => setSelectedTopicId(t.id)}
                          className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start justify-between ${
                            selectedTopicId === t.id
                              ? "bg-blue-950/30 border-blue-500/70 shadow-md shadow-blue-500/10"
                              : "bg-slate-950 border-slate-800/80 hover:border-slate-700"
                          }`}
                        >
                          <div>
                            <h4 className="font-semibold text-sm text-white">{t.theme}</h4>
                            <p className="text-xs text-slate-400 mt-1">
                              Part 1: {t.part1_topics?.join(", ")}
                            </p>
                            <p className="text-xs text-slate-500 mt-0.5 line-clamp-1 italic">
                              "{t.part2_cue_card_title}"
                            </p>
                          </div>
                          <div className="shrink-0 mt-1">
                            <input
                              type="radio"
                              name="topic"
                              checked={selectedTopicId === t.id}
                              onChange={() => setSelectedTopicId(t.id)}
                              className="w-4 h-4 text-blue-600 cursor-pointer"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={handleStartExam}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3.5 px-6 rounded-xl shadow-lg shadow-blue-500/25 transition-all cursor-pointer disabled:opacity-50"
                  >
                    <PlayCircle className="w-5 h-5" />
                    <span>{isLoading ? "Initializing Examiner..." : "Begin IELTS Mock Test"}</span>
                  </button>
                </div>
              </div>
            )}

            {/* VIEW 2: INTERACTIVE INTERVIEW ROOM */}
            {viewState === "INTERVIEW" && currentAction && (
              <div className="space-y-6 animate-in fade-in duration-300">
                {/* Stage Status Bar */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
                    <span className="text-xs font-bold tracking-wider uppercase text-blue-400">
                      {getStageLabel(currentAction.stage)}
                    </span>
                  </div>
                  <button
                    onClick={handleScoreExam}
                    disabled={isLoading}
                    className="flex items-center gap-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-1.5 rounded-lg shadow-sm transition-all cursor-pointer"
                  >
                    <FileCheck2 className="w-3.5 h-3.5" />
                    <span>Finish & Get Score</span>
                  </button>
                </div>

                {/* Examiner Speech Card */}
                <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-blue-500 text-white flex items-center justify-center font-bold text-lg shrink-0 shadow-lg shadow-indigo-500/20">
                      Dr. E
                    </div>
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-400">Certified IELTS Examiner</span>
                        <button
                          onClick={() => speakExaminerUtterance(currentAction.utterance)}
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 cursor-pointer"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                          <span>Replay Audio</span>
                        </button>
                      </div>
                      <p className="text-base text-slate-100 font-medium leading-relaxed whitespace-pre-line">
                        {currentAction.utterance}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Candidate Response Workspace */}
                <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                      <Mic className="w-4 h-4 text-blue-400" />
                      Your Turn: Speak Your Answer
                    </h3>
                    <span className="text-xs text-slate-400 font-mono">
                      {isRecording ? `Spoken Duration: ${recordingDuration}s` : "Press Record when ready"}
                    </span>
                  </div>

                  {/* Audio Waveform Canvas */}
                  <AudioWaveform
                    isRecording={isRecording}
                    stream={audioStream}
                    durationSeconds={recordingDuration}
                  />

                  {/* Spoken / Transcribed Text Editor */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-slate-400">Verbatim Speech Transcript:</span>
                      {isTranscribing && (
                        <span className="text-xs text-blue-400 flex items-center gap-1.5 font-medium animate-pulse">
                          <span className="w-2 h-2 rounded-full bg-blue-500" />
                          AI Transcribing Spoken Audio...
                        </span>
                      )}
                    </div>
                    <textarea
                      value={candidateText}
                      onChange={(e) => setCandidateText(e.target.value)}
                      placeholder="Your speech transcript will appear here in real-time as you speak, or you can type here directly..."
                      className="w-full h-32 bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none font-mono"
                    />
                  </div>

                  {/* Controls */}
                  <div className="flex items-center justify-between gap-4">
                    <button
                      onClick={handleToggleRecording}
                      className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer shadow-md ${
                        isRecording
                          ? "bg-red-600 hover:bg-red-500 text-white shadow-red-500/20"
                          : "bg-slate-800 hover:bg-slate-700 text-white border border-slate-700"
                      }`}
                    >
                      {isRecording ? (
                        <>
                          <MicOff className="w-4 h-4 text-red-200" />
                          <span>Pause / Stop Recording</span>
                        </>
                      ) : (
                        <>
                          <Mic className="w-4 h-4 text-blue-400" />
                          <span>Start Speaking (Record)</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={handleSubmitResponse}
                      disabled={isLoading || !candidateText.trim()}
                      className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm px-6 py-2.5 rounded-xl shadow-lg shadow-blue-500/20 transition-all cursor-pointer disabled:opacity-40"
                    >
                      <span>{isLoading ? "Processing..." : "Submit Response"}</span>
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Cue Card Modal for Part 2 */}
                {showCueCard && currentAction.display_cue_card && (
                  <CueCardModal
                    cueCard={currentAction.display_cue_card}
                    onPrepComplete={handleCueCardPrepComplete}
                  />
                )}
              </div>
            )}

            {/* VIEW 3: COMPREHENSIVE DIAGNOSTIC SCORECARD */}
            {viewState === "SCORECARD" && scorecardData && (
              <ScorecardView
                scorecard={scorecardData}
                markdownReport={markdownReport}
                onReset={() => {
                  setViewState("SETUP");
                  setSessionId(null);
                  setCurrentAction(null);
                  setScorecardData(null);
                }}
              />
            )}
          </>
        )}

        {/* MODULE 2: WRITING */}
        {activeModule === "writing" && (
          <div className="max-w-4xl mx-auto w-full space-y-6 animate-in fade-in duration-300">
            <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-3xl p-8 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                    BandIT Writing Module
                  </span>
                  <h2 className="text-2xl font-extrabold text-white mt-2">IELTS Academic & General Writing</h2>
                  <p className="text-sm text-slate-400 mt-1 max-w-xl">
                    Master Task 1 reports/letters and Task 2 discursive essays with automated Coherence & Cohesion (CC) and Lexical Resource (LR) grading.
                  </p>
                </div>
                <PenTool className="w-12 h-12 text-blue-400/40" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800/80">
                  <h3 className="font-bold text-white text-base">Task 1 (Report or Letter)</h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                    20 minutes • Minimum 150 words • Report main trends in charts/tables or compose a formal/semi-formal letter.
                  </p>
                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                    <span>Weight: 33% of Writing Band</span>
                    <span className="text-blue-400 font-semibold">150+ Words</span>
                  </div>
                </div>

                <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800/80">
                  <h3 className="font-bold text-white text-base">Task 2 (Discursive Essay)</h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                    40 minutes • Minimum 250 words • Present a clear opinion, evaluate arguments, and justify with relevant examples.
                  </p>
                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                    <span>Weight: 67% (2x Task 1)</span>
                    <span className="text-emerald-400 font-semibold">250+ Words</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 rounded-xl bg-blue-950/20 border border-blue-800/30 flex items-center justify-between text-xs text-slate-300">
                <span>Writing Formula: <code className="text-blue-400 font-mono">Writing Band = (Task 1 + 2 * Task 2) / 3</code></span>
                <span className="text-emerald-400 font-semibold">AI Grading Ready</span>
              </div>
            </div>
          </div>
        )}

        {/* MODULE 3: READING */}
        {activeModule === "reading" && (
          <div className="max-w-4xl mx-auto w-full space-y-6 animate-in fade-in duration-300">
            <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-3xl p-8 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                    BandIT Reading Module
                  </span>
                  <h2 className="text-2xl font-extrabold text-white mt-2">IELTS Reading Comprehension</h2>
                  <p className="text-sm text-slate-400 mt-1 max-w-xl">
                    60 minutes • 3 Academic Passages • 40 Questions (True/False/Not Given, Heading Matching, Sentence Completion).
                  </p>
                </div>
                <BookOpen className="w-12 h-12 text-blue-400/40" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
                  <h4 className="font-bold text-white text-sm">Passage 1</h4>
                  <p className="text-xs text-slate-400 mt-1">Factual & Descriptive context</p>
                  <span className="text-xs text-blue-400 font-mono block mt-3">Questions 1–13</span>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
                  <h4 className="font-bold text-white text-sm">Passage 2</h4>
                  <p className="text-xs text-slate-400 mt-1">Analytical & Work-related text</p>
                  <span className="text-xs text-blue-400 font-mono block mt-3">Questions 14–26</span>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
                  <h4 className="font-bold text-white text-sm">Passage 3</h4>
                  <p className="text-xs text-slate-400 mt-1">Complex Discursive argument</p>
                  <span className="text-xs text-blue-400 font-mono block mt-3">Questions 27–40</span>
                </div>
              </div>

              <div className="mt-6 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>Academic Target: 30/40 = Band 7.0 | 35/40 = Band 8.0</span>
                <span className="text-emerald-400 font-semibold">Instant Auto-Scoring</span>
              </div>
            </div>
          </div>
        )}

        {/* MODULE 4: LISTENING */}
        {activeModule === "listening" && (
          <div className="max-w-4xl mx-auto w-full space-y-6 animate-in fade-in duration-300">
            <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-3xl p-8 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                    BandIT Listening Module
                  </span>
                  <h2 className="text-2xl font-extrabold text-white mt-2">IELTS Listening Assessment</h2>
                  <p className="text-sm text-slate-400 mt-1 max-w-xl">
                    30 minutes audio • 4 Recorded Sections • British, Australian, and North American speaker accents.
                  </p>
                </div>
                <Headphones className="w-12 h-12 text-blue-400/40" />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8">
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/80">
                  <span className="text-xs font-bold text-white block">Section 1</span>
                  <span className="text-[11px] text-slate-400">Social Dialogue</span>
                  <span className="text-xs text-blue-400 font-mono block mt-2">Q 1–10</span>
                </div>
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/80">
                  <span className="text-xs font-bold text-white block">Section 2</span>
                  <span className="text-[11px] text-slate-400">Local Monologue</span>
                  <span className="text-xs text-blue-400 font-mono block mt-2">Q 11–20</span>
                </div>
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/80">
                  <span className="text-xs font-bold text-white block">Section 3</span>
                  <span className="text-[11px] text-slate-400">Academic Discussion</span>
                  <span className="text-xs text-blue-400 font-mono block mt-2">Q 21–30</span>
                </div>
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/80">
                  <span className="text-xs font-bold text-white block">Section 4</span>
                  <span className="text-[11px] text-slate-400">University Lecture</span>
                  <span className="text-xs text-blue-400 font-mono block mt-2">Q 31–40</span>
                </div>
              </div>

              <div className="mt-6 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>Listening Target: 30/40 = Band 7.0 | 35/40 = Band 8.0</span>
                <span className="text-emerald-400 font-semibold">Strict Spelling Sensitivity</span>
              </div>
            </div>
          </div>
        )}

        {/* AI Model & Keys Settings Modal */}
        <SettingsModal
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
        />
      </main>
    </div>
  );
}
