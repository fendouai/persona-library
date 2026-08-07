"use client";

import { useState } from "react";
import { rewrite, type Persona, type RewriteResult } from "@/lib/api";

const TONE_LABELS: Record<string, string> = {
  formality: "Formality",
  warmth: "Warmth",
  confidence: "Confidence",
  humor: "Humor",
  emotional_intensity: "Emotional intensity",
  directness: "Directness",
};

export default function RewriteForm({
  persona,
  defaultText,
}: {
  persona: Persona;
  defaultText?: string;
}) {
  const [text, setText] = useState(defaultText ?? "");
  const [strength, setStrength] = useState(persona.style_strength_default ?? 0.7);
  const [platform, setPlatform] = useState("generic");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RewriteResult | null>(null);

  async function run() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await rewrite({
        persona_id: persona.id,
        text,
        style_strength: strength,
        platform,
        preserve_length: true,
        candidate_count: 3,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h3 className="mb-1 font-medium">Rewrite with {persona.name}</h3>
        <div className="mb-4 flex flex-wrap gap-2 text-xs text-zinc-500">
          {Object.entries(TONE_LABELS).map(([k, label]) => (
            <span key={k} title={label}>
              {label}: {(persona.profile.tone[k as keyof typeof persona.profile.tone] * 100).toFixed(0)}
            </span>
          ))}
        </div>
        <textarea
          className="input min-h-40 font-mono text-[13px] leading-relaxed"
          placeholder="Paste the text you want rewritten…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="mt-3 flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-zinc-400">
            Style strength
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={strength}
              onChange={(e) => setStrength(Number(e.target.value))}
              className="w-36 accent-amber-400"
            />
            <span className="font-mono text-xs text-zinc-300">{strength.toFixed(2)}</span>
          </label>
          <label className="flex items-center gap-2 text-sm text-zinc-400">
            Platform
            <select
              className="input w-auto py-1.5"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              {["generic", "x", "linkedin", "email", "blog", "newsletter", "academic"].map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <button className="btn" onClick={run} disabled={loading || !text.trim()}>
            {loading ? "Rewriting…" : "Rewrite"}
          </button>
        </div>
        {error && (
          <p className="mt-3 rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}
      </div>

      {result && (
        <div>
          <div className="mb-3 grid grid-cols-4 gap-2">
            {[
              ["Meaning", result.scores.meaning_preservation],
              ["Style", result.scores.style_match],
              ["Readability", result.scores.readability],
              ["Platform", result.scores.platform_fit],
            ].map(([label, value]) => (
              <div key={String(label)} className="card !p-3">
                <p className="text-xs text-zinc-500">{label}</p>
                <p className="mt-0.5 font-mono text-lg">{(Number(value) * 100).toFixed(0)}</p>
                <div className="mt-1.5 h-1 overflow-hidden rounded bg-zinc-800">
                  <div
                    className="h-full bg-amber-400"
                    style={{ width: `${Number(value) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="card !p-0">
            <div className="border-b border-zinc-800 px-4 py-2 text-xs text-zinc-500">
              Final score: {(result.scores.final_score * 100).toFixed(0)} / 100
              <span className="ml-2 text-zinc-600">
                (0.45 meaning + 0.30 style + 0.15 readability + 0.10 platform)
              </span>
            </div>
            <pre className="whitespace-pre-wrap px-4 py-4 font-mono text-[13px] leading-relaxed text-zinc-200">
              {result.output}
            </pre>
            <button
              className="m-4 mt-0 text-xs text-amber-400 hover:text-amber-300"
              onClick={() => navigator.clipboard.writeText(result.output)}
            >
              Copy to clipboard
            </button>
          </div>
          {result.alternatives.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-sm text-zinc-500 hover:text-zinc-300">
                {result.alternatives.length} alternative candidate(s)
              </summary>
              {result.alternatives.map((alt, i) => (
                <pre
                  key={i}
                  className="mt-2 whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3 font-mono text-xs text-zinc-400"
                >
                  {alt}
                </pre>
              ))}
            </details>
          )}
        </div>
      )}
    </div>
  );
}
