"use client";

import React, { useState, useEffect } from "react";
import { Clock, Edit3, ArrowRight, CheckCircle2 } from "lucide-react";

interface CueCardModalProps {
  cueCard: {
    title: string;
    prompts: string[];
    prep_time_seconds: number;
    target_speaking_seconds: number;
  };
  onPrepComplete: () => void;
}

export default function CueCardModal({
  cueCard,
  onPrepComplete,
}: CueCardModalProps) {
  const [timeLeft, setTimeLeft] = useState<number>(cueCard.prep_time_seconds || 60);
  const [notes, setNotes] = useState<string>("");

  useEffect(() => {
    if (timeLeft <= 0) {
      onPrepComplete();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          onPrepComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, onPrepComplete]);

  const progressPercent = Math.max(0, (timeLeft / (cueCard.prep_time_seconds || 60)) * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-300">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-900/60 to-indigo-900/60 border-b border-slate-800 p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold tracking-wider uppercase text-blue-400 bg-blue-950/70 border border-blue-800/50 px-2.5 py-0.5 rounded-full">
              IELTS Speaking Part 2
            </span>
            <h2 className="text-xl font-bold text-white mt-1">Individual Long Turn (Cue Card)</h2>
          </div>

          {/* Countdown Clock */}
          <div className="flex items-center gap-2 bg-slate-950/70 border border-slate-700 px-3.5 py-1.5 rounded-xl">
            <Clock className={`w-5 h-5 ${timeLeft <= 10 ? "text-red-400 animate-bounce" : "text-amber-400"}`} />
            <div className="flex flex-col items-end">
              <span className="text-xs text-slate-400 font-medium">Prep Time</span>
              <span className={`font-mono text-lg font-bold leading-none ${timeLeft <= 10 ? "text-red-400" : "text-amber-300"}`}>
                0:{timeLeft < 10 ? "0" : ""}{timeLeft}
              </span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-800 h-1.5">
          <div
            className={`h-full transition-all duration-1000 ${
              timeLeft <= 10 ? "bg-red-500" : "bg-blue-500"
            }`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[70vh]">
          {/* Cue Card Prompt Box */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 shadow-inner">
            <h3 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              {cueCard.title}
            </h3>

            <p className="text-sm font-medium text-slate-400 mb-2">You should say:</p>
            <ul className="space-y-1.5 text-sm text-slate-300">
              {cueCard.prompts.map((prompt, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-blue-400 font-bold">•</span>
                  <span>{prompt}</span>
                </li>
              ))}
            </ul>

            <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs text-slate-400 flex items-center justify-between">
              <span>Speaking Target: 1 to 2 minutes</span>
              <span>Preparation: 1 minute</span>
            </div>
          </div>

          {/* Digital Scratchpad for Candidate Notes */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
              <Edit3 className="w-4 h-4 text-blue-400" />
              Digital Scratchpad (make bullet notes while you prepare):
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Jot down key points, keywords, and collocations you want to include..."
              className="w-full h-28 bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none font-mono"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="bg-slate-950 border-t border-slate-800 p-4 flex items-center justify-between">
          <p className="text-xs text-slate-400">
            When the timer hits 0:00, you will be asked to begin speaking.
          </p>
          <button
            onClick={onPrepComplete}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-sm px-5 py-2.5 rounded-xl shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
          >
            <span>I'm Ready to Speak</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
