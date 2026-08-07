"use client";

import { useEffect, useMemo, useState } from "react";
import { listPersonas, mixPreview, rewrite, type Persona, type RewriteResult } from "@/lib/api";

const TONE_KEYS = [
  "formality",
  "warmth",
  "confidence",
  "humor",
  "emotional_intensity",
  "directness",
] as const;

export default function MixPage() {
  const [all, setAll] = useState<Persona[]>([]);
  const [rows, setRows] = useState<{ id: string; weight: number }[]>([
    { id: "", weight: 70 },
    { id: "", weight: 30 },
  ]);
  const [text, setText] = useState("");
  const [blend, setBlend] = useState<Persona | null>(null);
  const [result, setResult] = useState<RewriteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listPersonas().then((d) => setAll(d.personas)).catch(() => {});
  }, []);

  const ready = rows.filter((r) => r.id).length >= 2;
  const totalWeight = rows.reduce((s, r) => s + r.weight, 0);

  const validRows = useMemo(
    () => rows.filter((r) => r.id).map((r) => ({ id: r.id, weight: r.weight / totalWeight })),
    [rows, totalWeight]
  );

  async function preview() {
    setError(null);
    setResult(null);
    try {
      const blended = await mixPreview(validRows);
      setBlend(blended);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function runRewrite() {
    if (!blend || !text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await rewrite({
        persona: blend,
        text,
        style_strength: 0.8,
        platform: "generic",
        candidate_count: 3,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function updateRow(i: number, patch: Partial<{ id: string; weight: number }>) {
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
    setBlend(null);
    setResult(null);
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Mix Personas</h1>
      <p className="mt-1 max-w-2xl text-sm text-zinc-400">
        Blend two or more personas into one temporary profile — tone dimensions
        are weighted-averaged, vocabulary and patterns merged by weight.
      </p>

      <div className="mt-6 space-y-3">
        {rows.map((row, i) => (
          <div key={i} className="flex items-center gap-3">
            <select
              className="input flex-1"
              value={row.id}
              onChange={(e) => updateRow(i, { id: e.target.value })}
            >
              <option value="">Select a persona…</option>
              {all.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.emoji ?? "•"} {p.name}
                </option>
              ))}
            </select>
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <input
                type="number"
                min={1}
                max={100}
                value={row.weight}
                onChange={(e) => updateRow(i, { weight: Number(e.target.value) })}
                className="input w-20"
              />
              %
            </div>
            <button
              className="btn-ghost"
              onClick={() => setRows((prev) => prev.filter((_, idx) => idx !== i))}
              disabled={rows.length <= 2}
            >
              ✕
            </button>
          </div>
        ))}
        <button className="btn-ghost" onClick={() => setRows((prev) => [...prev, { id: "", weight: 50 }])}>
          + Add persona
        </button>
      </div>

      <button className="btn mt-6" onClick={preview} disabled={!ready}>
        Preview blend
      </button>

      {blend && (
        <div className="card mt-6">
          <h2 className="mb-3 font-medium">Blended profile</h2>
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-3">
            {TONE_KEYS.map((k) => (
              <div key={k} className="flex items-center justify-between gap-2 text-sm">
                <span className="text-zinc-400">{k}</span>
                <span className="font-mono text-zinc-200">
                  {((blend.profile.tone[k] ?? 0) * 100).toFixed(0)}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-zinc-500">
            Voice: {blend.profile.voice_summary}
          </p>
          <textarea
            className="input mt-4 min-h-32 font-mono text-[13px]"
            placeholder="Text to rewrite with the blended voice…"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button className="btn mt-3" onClick={runRewrite} disabled={loading || !text.trim()}>
            {loading ? "Rewriting…" : "Rewrite with blend"}
          </button>
          {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
          {result && (
            <div className="mt-4">
              <p className="mb-2 text-xs text-zinc-500">
                Final score: {(result.scores.final_score * 100).toFixed(0)} / 100
              </p>
              <pre className="whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-3 font-mono text-[13px] text-zinc-200">
                {result.output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
