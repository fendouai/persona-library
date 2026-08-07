import { listPersonas } from "@/lib/api";
import PersonaBrowser from "@/components/PersonaBrowser";
import { Suspense } from "react";

export const dynamic = "force-dynamic";

export default async function BrowsePage() {
  const { personas, count } = await listPersonas();
  const categories = Array.from(new Set(personas.map((p) => p.category))).sort();

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Persona Library</h1>
        <p className="mt-1 text-sm text-zinc-400">
          {count} writing personas. Choose one, feed it text, and get a
          rewrite that matches the persona's voice without changing the facts.
        </p>
      </div>
      <Suspense>
        <PersonaBrowser initial={personas} categories={categories} />
      </Suspense>
    </div>
  );
}
