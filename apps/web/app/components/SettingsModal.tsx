"use client";

import React, { useState, useEffect } from "react";
import { X, Key, Cpu, CheckCircle2, AlertCircle, ExternalLink, Loader2, Zap } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSettingsSaved?: () => void;
}

export default function SettingsModal({ isOpen, onClose, onSettingsSaved }: SettingsModalProps) {
  const [provider, setProvider] = useState<"gemini" | "openai">("gemini");
  const [model, setModel] = useState<string>("gemini-1.5-pro");
  const [apiKey, setApiKey] = useState<string>("");
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [configuredInfo, setConfiguredInfo] = useState<any>(null);

  const API_BASE = "http://127.0.0.1:8000";

  useEffect(() => {
    if (isOpen) {
      fetch(`${API_BASE}/api/settings`)
        .then((res) => res.json())
        .then((data) => {
          setConfiguredInfo(data);
          if (data.gemini_configured) {
            setProvider("gemini");
            setModel(data.gemini_model || "gemini-1.5-pro");
            setApiKey(data.gemini_masked_key || "");
          } else if (data.openai_configured) {
            setProvider("openai");
            setModel(data.openai_model || "gpt-4o");
            setApiKey(data.openai_masked_key || "");
          }
        })
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setIsTesting(true);
    setStatusMessage({ type: "info", text: "Connecting to live frontier LLM..." });
    try {
      const res = await fetch(`${API_BASE}/api/settings/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          api_key: apiKey.includes("...") ? undefined : apiKey,
          model,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setStatusMessage({
          type: "success",
          text: `Live connected to ${data.model} in ${data.latency_ms}ms! Model responded: "${data.reply}"`,
        });
      } else {
        setStatusMessage({
          type: "error",
          text: data.error || "Connection test failed. Please verify API key.",
        });
      }
    } catch (e: any) {
      setStatusMessage({ type: "error", text: `Connection error: ${e.message}` });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await fetch(`${API_BASE}/api/settings/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          api_key: apiKey.includes("...") ? "" : apiKey,
          model,
        }),
      });
      setStatusMessage({ type: "success", text: "Configuration saved to environment and .env file!" });
      if (onSettingsSaved) onSettingsSaved();
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (e: any) {
      setStatusMessage({ type: "error", text: `Failed to save: ${e.message}` });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700 rounded-3xl max-w-lg w-full shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-slate-950 border-b border-slate-800 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Zap className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white leading-tight">Live Frontier LLM Settings</h3>
              <p className="text-xs text-slate-400">Configure Gemini 1.5 Pro or GPT-4o for live grading</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Provider Selection */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
              Model Provider
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => {
                  setProvider("gemini");
                  setModel("gemini-1.5-pro");
                  setStatusMessage(null);
                }}
                className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                  provider === "gemini"
                    ? "bg-blue-950/40 border-blue-500 shadow-md shadow-blue-500/10 text-white"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm">Google Gemini</span>
                  <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Recommended</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">Gemini 1.5 Pro / 2.5 Flash</p>
              </button>

              <button
                type="button"
                onClick={() => {
                  setProvider("openai");
                  setModel("gpt-4o");
                  setStatusMessage(null);
                }}
                className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                  provider === "openai"
                    ? "bg-blue-950/40 border-blue-500 shadow-md shadow-blue-500/10 text-white"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <span className="font-bold text-sm block">OpenAI</span>
                <p className="text-xs text-slate-400 mt-1">GPT-4o</p>
              </button>
            </div>
          </div>

          {/* Model Dropdown */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1.5">
              Specific Model Engine
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer"
            >
              {provider === "gemini" ? (
                <>
                  <option value="gemini-1.5-pro">Gemini 1.5 Pro (Deepest linguistic analysis & rubric grounding)</option>
                  <option value="gemini-2.5-flash">Gemini 2.5 Flash (Ultra low-latency evaluation)</option>
                </>
              ) : (
                <>
                  <option value="gpt-4o">GPT-4o (Omni multimodal model)</option>
                  <option value="gpt-4o-mini">GPT-4o Mini (Cost-efficient)</option>
                </>
              )}
            </select>
          </div>

          {/* API Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-blue-400" />
                {provider === "gemini" ? "Gemini API Key" : "OpenAI API Key"}
              </label>
              {provider === "gemini" && (
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] text-blue-400 hover:underline flex items-center gap-1"
                >
                  <span>Get free key</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={provider === "gemini" ? "AIzaSy..." : "sk-..."}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Your API key is stored securely in your local <code className="text-slate-400">.env</code> file.
            </p>
          </div>

          {/* Feedback banner */}
          {statusMessage && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 leading-relaxed ${
                statusMessage.type === "success"
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                  : statusMessage.type === "error"
                  ? "bg-rose-950/40 border-rose-500/40 text-rose-300"
                  : "bg-blue-950/40 border-blue-500/40 text-blue-300"
              }`}
            >
              {statusMessage.type === "success" && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />}
              {statusMessage.type === "error" && <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
              {statusMessage.type === "info" && <Loader2 className="w-4 h-4 text-blue-400 shrink-0 mt-0.5 animate-spin" />}
              <span>{statusMessage.text}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-950 border-t border-slate-800 p-4 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={isTesting}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition cursor-pointer disabled:opacity-50"
          >
            {isTesting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>Test Connection</span>
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 text-white font-semibold text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-blue-500/20 transition cursor-pointer disabled:opacity-50"
          >
            {isSaving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>Save & Apply Settings</span>
          </button>
        </div>
      </div>
    </div>
  );
}
