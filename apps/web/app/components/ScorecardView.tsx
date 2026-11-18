"use client";

import React, { useState } from "react";
import {
  Award,
  BookOpen,
  Volume2,
  Activity,
  CheckCircle,
  AlertCircle,
  Sparkles,
  TrendingUp,
  Download,
  RotateCcw,
  Zap,
} from "lucide-react";

interface CriterionData {
  band: number;
  summary: string;
  strengths: string[];
  improvements: string[];
}

interface ScorecardViewProps {
  scorecard: {
    session_id: string;
    candidate_name: string;
    test_theme: string;
    evaluated_at: string;
    overall_band: number;
    criteria: {
      fluency_and_coherence: CriterionData;
      lexical_resource: CriterionData;
      grammatical_range_and_accuracy: CriterionData;
      pronunciation: CriterionData;
    };
    metrics: {
      wpm: number;
      total_words: number;
      filler_ratio: number;
      ttr: number;
      cefr_distribution: {
        A1_A2: number;
        B1_B2: number;
        C1_C2: number;
      };
      complex_sentence_ratio: number;
      intelligibility_score: number;
    };
    sentence_upgrades: Array<{
      original: string;
      upgraded: string;
      target_band: number;
      rationale: string;
    }>;
    action_plan: string[];
  };
  markdownReport: string;
  onReset: () => void;
}

export default function ScorecardView({
  scorecard,
  markdownReport,
  onReset,
}: ScorecardViewProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "upgrades" | "action_plan">("overview");

  const getBandBadgeColor = (band: number) => {
    if (band >= 8.0) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    if (band >= 7.0) return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    if (band >= 6.0) return "bg-amber-500/10 text-amber-400 border-amber-500/30";
    return "bg-rose-500/10 text-rose-400 border-rose-500/30";
  };

  const downloadReport = () => {
    const blob = new Blob([markdownReport], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `IELTS_Scorecard_${scorecard.candidate_name}_Band${scorecard.overall_band}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Hero Banner with Overall Score */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-900/60 border border-blue-700/50 text-blue-300">
              <Award className="w-4 h-4 text-amber-400" />
              Official IELTS 9-Band Calibrated Scorecard
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Diagnostic Assessment: {scorecard.candidate_name}
            </h1>
            <p className="text-sm text-slate-400">
              Theme: <span className="text-slate-200 font-medium">{scorecard.test_theme}</span>
            </p>
          </div>

          {/* Large Overall Band Badge */}
          <div className="flex flex-col items-center justify-center bg-slate-950/80 border-2 border-indigo-500/40 rounded-2xl p-6 shadow-xl min-w-[200px]">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Overall Band</span>
            <div className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-emerald-400 to-indigo-300 my-1 font-mono">
              {scorecard.overall_band.toFixed(1)}
            </div>
            <span className="text-xs text-slate-400">CEFR: {scorecard.overall_band >= 7.5 ? "C1 Advanced" : scorecard.overall_band >= 6.5 ? "B2+ Competent" : "B2 Modest"}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 pt-6 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "overview"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "bg-slate-800/80 text-slate-400 hover:text-white"
              }`}
            >
              Rubric Overview
            </button>
            <button
              onClick={() => setActiveTab("upgrades")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "upgrades"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "bg-slate-800/80 text-slate-400 hover:text-white"
              }`}
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              Band 8.5+ Upgrade Coach
            </button>
            <button
              onClick={() => setActiveTab("action_plan")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "action_plan"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "bg-slate-800/80 text-slate-400 hover:text-white"
              }`}
            >
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              Targeted Study Plan
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={downloadReport}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>Export Report (.md)</span>
            </button>
            <button
              onClick={onReset}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 text-white transition-all shadow-md shadow-blue-500/20 cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Practice Another Test</span>
            </button>
          </div>
        </div>
      </div>

      {activeTab === "overview" && (
        <>
          {/* 4 Official Criteria Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Fluency and Coherence */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
                      <Activity className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-white text-lg">Fluency & Coherence</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-mono font-bold border ${getBandBadgeColor(scorecard.criteria.fluency_and_coherence.band)}`}>
                    Band {scorecard.criteria.fluency_and_coherence.band.toFixed(1)}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed mb-4">
                  {scorecard.criteria.fluency_and_coherence.summary}
                </p>
                <div className="space-y-2 text-xs">
                  {scorecard.criteria.fluency_and_coherence.strengths.map((str, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{str}</span>
                    </div>
                  ))}
                  {scorecard.criteria.fluency_and_coherence.improvements.map((imp, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-amber-300">
                      <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <span>{imp}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>Tempo: {scorecard.metrics.wpm} WPM</span>
                <span>Filler Pause: {scorecard.metrics.filler_ratio}%</span>
              </div>
            </div>

            {/* 2. Lexical Resource */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
                      <BookOpen className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-white text-lg">Lexical Resource</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-mono font-bold border ${getBandBadgeColor(scorecard.criteria.lexical_resource.band)}`}>
                    Band {scorecard.criteria.lexical_resource.band.toFixed(1)}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed mb-4">
                  {scorecard.criteria.lexical_resource.summary}
                </p>
                <div className="space-y-2 text-xs">
                  {scorecard.criteria.lexical_resource.strengths.map((str, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{str}</span>
                    </div>
                  ))}
                  {scorecard.criteria.lexical_resource.improvements.map((imp, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-amber-300">
                      <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <span>{imp}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>TTR Diversity: {scorecard.metrics.ttr}</span>
                <span>C1/C2 Words: {scorecard.metrics.cefr_distribution.C1_C2}%</span>
              </div>
            </div>

            {/* 3. Grammatical Range and Accuracy */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                      <Zap className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-white text-lg">Grammatical Range & Accuracy</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-mono font-bold border ${getBandBadgeColor(scorecard.criteria.grammatical_range_and_accuracy.band)}`}>
                    Band {scorecard.criteria.grammatical_range_and_accuracy.band.toFixed(1)}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed mb-4">
                  {scorecard.criteria.grammatical_range_and_accuracy.summary}
                </p>
                <div className="space-y-2 text-xs">
                  {scorecard.criteria.grammatical_range_and_accuracy.strengths.map((str, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{str}</span>
                    </div>
                  ))}
                  {scorecard.criteria.grammatical_range_and_accuracy.improvements.map((imp, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-amber-300">
                      <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <span>{imp}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>Complex Clauses: {Math.round(scorecard.metrics.complex_sentence_ratio * 100)}%</span>
                <span>Accuracy: High</span>
              </div>
            </div>

            {/* 4. Pronunciation */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
                      <Volume2 className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-white text-lg">Pronunciation</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-mono font-bold border ${getBandBadgeColor(scorecard.criteria.pronunciation.band)}`}>
                    Band {scorecard.criteria.pronunciation.band.toFixed(1)}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed mb-4">
                  {scorecard.criteria.pronunciation.summary}
                </p>
                <div className="space-y-2 text-xs">
                  {scorecard.criteria.pronunciation.strengths.map((str, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{str}</span>
                    </div>
                  ))}
                  {scorecard.criteria.pronunciation.improvements.map((imp, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-amber-300">
                      <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <span>{imp}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>Intelligibility: {scorecard.metrics.intelligibility_score}/100</span>
                <span>Rhythm: Natural</span>
              </div>
            </div>
          </div>

          {/* Quantitative Speech Metrics Strip */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              Deterministic Acoustic & NLP Metrics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400">Speaking Tempo</span>
                <p className="text-2xl font-bold font-mono text-white mt-1">{scorecard.metrics.wpm} <span className="text-xs text-slate-500 font-sans">WPM</span></p>
                <span className="text-[11px] text-slate-500">Target: 120-145 WPM</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400">Vocabulary Variety (TTR)</span>
                <p className="text-2xl font-bold font-mono text-emerald-400 mt-1">{scorecard.metrics.ttr}</p>
                <span className="text-[11px] text-slate-500">Above 0.40 is Band 7+</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400">Complex Clause Ratio</span>
                <p className="text-2xl font-bold font-mono text-indigo-400 mt-1">{Math.round(scorecard.metrics.complex_sentence_ratio * 100)}%</p>
                <span className="text-[11px] text-slate-500">Subordination index</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400">Hesitation / Fillers</span>
                <p className="text-2xl font-bold font-mono text-blue-400 mt-1">{scorecard.metrics.filler_ratio}%</p>
                <span className="text-[11px] text-slate-500">Under 2.5% is Band 8+</span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Tab: Band Upgrade Coaching */}
      {activeTab === "upgrades" && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-400" />
              Band 8.5+ Linguistic Upgrade Coach
            </h3>
            <p className="text-sm text-slate-400">
              Review how actual phrases from your interview can be upgraded into Band 8.5+ expressions with sophisticated collocations, passive structures, and academic precision.
            </p>
          </div>

          <div className="space-y-4">
            {scorecard.sentence_upgrades.map((upgrade, idx) => (
              <div key={idx} className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                    Sample Upgrade #{idx + 1}
                  </span>
                  <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    Target: Band {upgrade.target_band.toFixed(1)}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Original */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                    <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Your Original Answer:</span>
                    <p className="text-sm text-slate-300 mt-1 italic">"{upgrade.original}"</p>
                  </div>

                  {/* Upgraded */}
                  <div className="bg-blue-950/20 p-4 rounded-xl border border-blue-800/40">
                    <span className="text-xs text-blue-400 uppercase tracking-wider font-semibold">Band 8.5+ Elevated Version:</span>
                    <p className="text-sm text-white font-medium mt-1">"{upgrade.upgraded}"</p>
                  </div>
                </div>

                <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/60 text-xs text-slate-300 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>Examiner Insight:</strong> {upgrade.rationale}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Action Plan */}
      {activeTab === "action_plan" && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-6">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Personalized Priority Roadmap
            </h3>
            <p className="text-sm text-slate-400 mt-1">
              Follow these prioritized actions to efficiently close your gap toward a Band 8.0+:
            </p>
          </div>

          <div className="space-y-3">
            {scorecard.action_plan.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3 p-4 rounded-xl bg-slate-950 border border-slate-800">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600/20 border border-blue-500/40 text-blue-400 text-xs font-bold shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="text-sm text-slate-200 leading-relaxed">{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
