import { getPersona } from "@/lib/api";
import Link from "next/link";
import { notFound } from "next/navigation";
import RewriteForm from "@/components/RewriteForm";

export const dynamic = "force-dynamic";

export default async function PersonaDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let persona;
  try {
    persona = await getPersona(id);
  } catch {
    notFound();
  }

  const tone = persona.profile.tone;
  const toneRows: [string, string, number][] = [
    ["Formality", "formality", tone.formality],
    ["Warmth", "warmth", tone.warmth],
    ["Confidence", "confidence", tone.confidence],
    ["Humor", "humor", tone.humor],
    ["Emotional intensity", "emotional_intensity", tone.emotional_intensity],
    ["Directness", "directness", tone.directness],
  ];

  return (
    <div>
      <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-300">
        ← All personas
      </Link>

      <div className="mt-4 flex items-start gap-4">
        <span className="text-4xl">{persona.emoji ?? "•"}</span>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{persona.name}</h1>
          <p className="mt-1 max-w-2xl text-sm text-zinc-400">{persona.description}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
            <span className="chip">{persona.category}</span>
            <span className="chip">v{persona.version}</span>
            <span className="chip">{persona.source_type}</span>
            {persona.languages.map((l) => (
              <span key={l} className="chip">{l}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="space-y-6 lg:col-span-2">
          <section className="card">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
              Tone Dimensions
            </h2>
            <div className="space-y-2.5">
              {toneRows.map(([label, key, value]) => (
                <div key={key}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-zinc-400">{label}</span>
                    <span className="font-mono text-zinc-500">{(value * 100).toFixed(0)}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded bg-zinc-800">
                    <div
                      className="h-full rounded bg-amber-400"
                      style={{ width: `${value * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="card">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
              Voice
            </h2>
            <p className="text-sm text-zinc-300">{persona.profile.voice_summary}</p>
          </section>

          <section className="card">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
              Vocabulary
            </h2>
            <p className="mb-1.5 text-xs text-zinc-500">Prefer</p>
            <div className="flex flex-wrap gap-1.5">
              {persona.profile.preferred_vocabulary.map((v) => (
                <span key={v} className="chip text-amber-300/80">{v}</span>
              ))}
            </div>
            <p className="mb-1.5 mt-4 text-xs text-zinc-500">Avoid</p>
            <div className="flex flex-wrap gap-1.5">
              {persona.profile.avoided_vocabulary.map((v) => (
                <span key={v} className="chip line-through decoration-red-400/60">{v}</span>
              ))}
            </div>
          </section>

          {persona.profile.anti_patterns.length > 0 && (
            <section className="card">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
                Anti-Patterns
              </h2>
              <ul className="list-inside list-disc space-y-1 text-sm text-zinc-400">
                {persona.profile.anti_patterns.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </section>
          )}

          {persona.profile.positive_examples.length > 0 && (
            <section className="card">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
                Examples
              </h2>
              <div className="space-y-4">
                {persona.profile.positive_examples.slice(0, 2).map((ex, i) => (
                  <div key={i} className="text-xs">
                    <p className="text-zinc-500">Input</p>
                    <blockquote className="mt-1 border-l-2 border-zinc-700 pl-3 text-zinc-400">
                      {ex.input}
                    </blockquote>
                    <p className="mt-2 text-zinc-500">Output</p>
                    <blockquote className="mt-1 border-l-2 border-amber-400/60 pl-3 text-amber-200/80">
                      {ex.output}
                    </blockquote>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        <div className="lg:col-span-3">
          <RewriteForm persona={persona} />
        </div>
      </div>
    </div>
  );
}
