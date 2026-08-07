import Link from "next/link";
import type { Persona } from "@/lib/api";

export default function PersonaCard({ persona }: { persona: Persona }) {
  return (
    <Link
      href={`/personas/${persona.id}`}
      className="card group block"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">{persona.emoji ?? "•"}</span>
          <div>
            <h3 className="font-medium group-hover:text-amber-300">
              {persona.name}
            </h3>
            <p className="text-xs text-zinc-500">{persona.category}</p>
          </div>
        </div>
      </div>
      <p className="mt-3 line-clamp-2 text-sm text-zinc-400">
        {persona.description}
      </p>
      <div className="mt-4 flex flex-wrap gap-1.5">
        {persona.tags.slice(0, 4).map((t) => (
          <span key={t} className="chip">
            {t}
          </span>
        ))}
      </div>
    </Link>
  );
}
