"use client";

import { useState } from "react";
import { createPersona, extractPersona, type Persona } from "@/lib/api";

const TONE_KEYS = [
  "formality",
  "warmth",
  "confidence",
  "humor",
  "emotional_intensity",
  "directness",
] as const;

export default function CreatePage() {
  const [tab, setTab] = useState<"samples" | "manual">("samples");

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Create a Persona</h1>
      <div className="mt-4 mb-8 flex gap-2">
        {(["samples", "manual"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-full px-4 py-1.5 text-sm transition-colors ${
              tab === t
                ? "bg-amber-400 text-zinc-950"
                : "border border-zinc-700 text-zinc-400 hover:border-zinc-500"
            }`}
          >
            {t === "samples" ? "From writing samples" : "Manual"}
          </button>
        ))}
      </div>
      {tab === "samples" ? <SampleExtract /> : <ManualCreate />}
    </div>
  );
}

function SampleExtract() {
  const [name, setName] = useState("");
  const [samples, setSamples] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<{
    persona: Persona;
    confidence: { overall: number; dimensions: Record<string, number>; warnings: string[] };
  } | null>(null);
  const [saved, setSaved] = useState(false);

  async function run() {
    const sampleList = samples.split(/\n---\n/).map((s) => s.trim()).filter(Boolean);
    if (sampleList.length === 0) {
      setError("Paste at least one sample. Separate multiple samples with a line of three dashes (---).");
      return;
    }
    setLoading(true);
    setError(null);
    setDraft(null);
    setSaved(false);
    try {
      const res = await extractPersona({ name: name || undefined, samples: sampleList });
      setDraft({ persona: res.persona, confidence: res.confidence });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function save() {
    if (!draft) return;
    try {
      await createPersona(draft.persona);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const high = Object.entries(draft?.confidence.dimensions ?? {})
    .filter(([, v]) => v >= 0.7)
    .sort((a, b) => b[1] - a[1]);
  const low = Object.entries(draft?.confidence.dimensions ?? {})
    .filter(([, v]) => v < 0.7)
    .sort((a, b) => a[1] - b[1]);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div>
        <label className="label">Persona name (optional)</label>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="My Writing Voice" />
        <label className="label mt-4">Writing samples</label>
        <textarea
          className="input min-h-64 font-mono text-[13px] leading-relaxed"
          placeholder={"Sample 1\n\n---\n\nSample 2\n\n---\n\nSample 3"}
          value={samples}
          onChange={(e) => setSamples(e.target.value)}
        />
        <p className="mt-2 text-xs text-zinc-500">
          Separate samples with a line of three dashes (---). 300+ words total gives more reliable style extraction.
        </p>
        <button className="btn mt-4" onClick={run} disabled={loading || !samples.trim()}>
          {loading ? "Analyzing style…" : "Extract persona"}
        </button>
        {error && (
          <p className="mt-3 rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}
      </div>

      {draft && (
        <div className="card space-y-4">
          <div>
            <h3 className="font-medium">
              {draft.persona.emoji ?? "✍️"} {draft.persona.name} — draft
            </h3>
            <p className="mt-1 text-sm text-zinc-400">{draft.persona.description}</p>
          </div>
          <div className="text-sm">
            <p className="mb-2 text-zinc-400">
              Confidence: <span className="font-mono text-amber-300">{(draft.confidence.overall * 100).toFixed(0)}%</span>
            </p>
            {high.length > 0 && (
              <div className="mb-2">
                <p className="mb-1 text-xs text-emerald-400">High confidence</p>
                <ul className="space-y-0.5 text-xs text-zinc-400">
                  {high.map(([k, v]) => <li key={k}>• {k}: {(v * 100).toFixed(0)}%</li>)}
                </ul>
              </div>
            )}
            {low.length > 0 && (
              <div>
                <p className="mb-1 text-xs text-amber-400">Low confidence</p>
                <ul className="space-y-0.5 text-xs text-zinc-400">
                  {low.map(([k, v]) => <li key={k}>• {k}: {(v * 100).toFixed(0)}%</li>)}
                </ul>
              </div>
            )}
            {draft.confidence.warnings.length > 0 && (
              <ul className="mt-2 space-y-0.5 text-xs text-zinc-500">
                {draft.confidence.warnings.map((w) => <li key={w}>⚠ {w}</li>)}
              </ul>
            )}
          </div>
          <p className="rounded-lg bg-zinc-900 px-3 py-2 text-xs text-zinc-400">
            Voice: {draft.persona.profile.voice_summary}
          </p>
          {saved ? (
            <p className="text-sm text-emerald-400">
              Saved to personas/custom/{draft.persona.id}.md
            </p>
          ) : (
            <button className="btn" onClick={save}>
              Save persona
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function ManualCreate() {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("custom");
  const [description, setDescription] = useState("");
  const [voice, setVoice] = useState("");
  const [tone, setTone] = useState<Record<string, number>>(
    Object.fromEntries(TONE_KEYS.map((k) => [k, 0.5])) as Record<string, number>
  );
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit() {
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }
    setError(null);
    const id = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    const persona: Persona = {
      id,
      name: name.trim(),
      description: description.trim() || `${name} writing persona.`,
      category,
      languages: ["en"],
      emoji: "✍️",
      version: "0.1.0",
      author: "user",
      license: "MIT",
      tags: [],
      source_type: "user-created",
      style_strength_default: 0.7,
      profile: {
        voice_summary: voice.trim() || "Describe the voice here.",
        tone: {
          formality: tone.formality,
          warmth: tone.warmth,
          confidence: tone.confidence,
          humor: tone.humor,
          emotional_intensity: tone.emotional_intensity,
          directness: tone.directness,
        },
        sentence_patterns: [],
        paragraph_patterns: [],
        rhetorical_patterns: [],
        preferred_vocabulary: [],
        avoided_vocabulary: [],
        signature_moves: [],
        anti_patterns: [],
        positive_examples: [],
        negative_examples: [],
      },
      content_preservation_rules: [],
      transformation_rules: [],
      body_markdown: "",
    };
    try {
      await createPersona(persona);
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="max-w-xl space-y-4">
      <label className="label">Name</label>
      <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Clear Product Thinker" />
      <label className="label">Category</label>
      <select className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
        {["custom", "archetypes", "creators", "brands", "professional", "personal", "founders", "educators", "journalists", "marketers", "social", "academic"].map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <label className="label">One-line description</label>
      <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
      <label className="label">Voice summary</label>
      <input className="input" value={voice} onChange={(e) => setVoice(e.target.value)} placeholder="Direct, practical, confident" />
      <div className="grid grid-cols-2 gap-4">
        {TONE_KEYS.map((k) => (
          <label key={k} className="flex flex-col gap-1 text-sm text-zinc-400">
            {k}
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={tone[k]}
                onChange={(e) => setTone({ ...tone, [k]: Number(e.target.value) })}
                className="w-full accent-amber-400"
              />
              <span className="w-8 font-mono text-xs">{tone[k].toFixed(2)}</span>
            </div>
          </label>
        ))}
      </div>
      {error && <p className="text-sm text-red-300">{error}</p>}
      {done ? (
        <p className="text-sm text-emerald-400">Created. You can now edit the markdown file in personas/custom/.</p>
      ) : (
        <button className="btn" onClick={submit}>Create persona</button>
      )}
    </div>
  );
}
