"use client";

import React, { useEffect, useRef } from "react";

interface AudioWaveformProps {
  isRecording: boolean;
  stream: MediaStream | null;
  durationSeconds: number;
}

export default function AudioWaveform({
  isRecording,
  stream,
  durationSeconds,
}: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  useEffect(() => {
    if (!isRecording) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      // Draw flat baseline
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.beginPath();
          ctx.moveTo(0, canvas.height / 2);
          ctx.lineTo(canvas.width, canvas.height / 2);
          ctx.strokeStyle = "#94a3b8";
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let analyser: AnalyserNode | null = null;

    if (stream) {
      try {
        const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        const audioCtx = new AudioContextClass();
        const source = audioCtx.createMediaStreamSource(stream);
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        source.connect(analyser);
        audioContextRef.current = audioCtx;
        analyserRef.current = analyser;
      } catch (err) {
        console.warn("Could not bind real audio stream to Web Audio context, falling back to simulated wave", err);
      }
    }

    const bufferLength = analyser ? analyser.frequencyBinCount : 32;
    const dataArray = new Uint8Array(bufferLength);

    let phase = 0;

    const render = () => {
      animationFrameRef.current = requestAnimationFrame(render);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (analyser) {
        analyser.getByteFrequencyData(dataArray);
      } else {
        // Simulated harmonic wave
        phase += 0.1;
        for (let i = 0; i < bufferLength; i++) {
          dataArray[i] = Math.sin(phase + i * 0.3) * 60 + 80;
        }
      }

      const barWidth = (canvas.width / bufferLength) * 0.7;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * (canvas.height * 0.85);

        // Gradient color from blue to emerald
        const gradient = ctx.createLinearGradient(0, canvas.height / 2 - barHeight / 2, 0, canvas.height / 2 + barHeight / 2);
        gradient.addColorStop(0, "#3b82f6");
        gradient.addColorStop(0.5, "#10b981");
        gradient.addColorStop(1, "#3b82f6");

        ctx.fillStyle = gradient;
        ctx.fillRect(
          x,
          canvas.height / 2 - barHeight / 2,
          barWidth,
          Math.max(barHeight, 4)
        );

        x += barWidth + 3;
      }
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, [isRecording, stream]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="flex flex-col items-center w-full">
      <div className="relative w-full h-20 bg-slate-900 rounded-xl overflow-hidden border border-slate-700 shadow-inner flex items-center justify-center">
        <canvas
          ref={canvasRef}
          width={450}
          height={80}
          className="w-full h-full"
        />
        {isRecording && (
          <div className="absolute top-2 right-3 flex items-center gap-2 bg-red-950/80 border border-red-500/50 px-2.5 py-1 rounded-full text-xs text-red-400 font-mono font-medium animate-pulse">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            REC {formatTime(durationSeconds)}
          </div>
        )}
      </div>
      <p className="text-xs text-slate-400 mt-1">
        {isRecording ? "Listening to your response... speak clearly into the microphone." : "Microphone idle."}
      </p>
    </div>
  );
}
