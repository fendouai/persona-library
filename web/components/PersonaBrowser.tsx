"use client";

import { useCallback, useEffect, useState } from "react";
import { listPersonas, type Persona } from "@/lib/api";
import PersonaCard from "./PersonaCard";

export default function PersonaBrowser({
  initial,
  categories,
}: {
  initial: Persona[];
  categories: string[];
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [personas, setPersonas] = useState(initial);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await listPersonas({
          query: query || undefined,
          category: category === "all" ? undefined : category,
        });
        setPersonas(data.personas);
      } catch {
        /* keep previous results */
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [query, category]);

  return (
    <div>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <input
          className="input"
          placeholder="Search personas…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="flex flex-wrap gap-1.5">
          {["all", ...categories].map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`rounded-full px-3 py-1 text-xs transition-colors ${
                category === c
                  ? "bg-amber-400 text-zinc-950"
                  : "border border-zinc-700 text-zinc-400 hover:border-zinc-500"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>
      {loading && (
        <p className="mb-4 text-xs text-zinc-500">Searching…</p>
      )}
      {personas.length === 0 ? (
        <p className="text-sm text-zinc-500">No personas found.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {personas.map((p) => (
            <PersonaCard key={p.id} persona={p} />
          ))}
        </div>
      )}
    </div>
  );
}
