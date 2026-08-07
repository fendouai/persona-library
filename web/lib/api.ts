export type Persona = {
  id: string;
  name: string;
  description: string;
  category: string;
  languages: string[];
  emoji: string | null;
  version: string;
  author: string;
  license: string;
  tags: string[];
  source_type: string;
  style_strength_default: number;
  profile: {
    voice_summary: string;
    tone: {
      formality: number;
      warmth: number;
      confidence: number;
      humor: number;
      emotional_intensity: number;
      directness: number;
    };
    sentence_patterns: string[];
    paragraph_patterns: string[];
    rhetorical_patterns: string[];
    preferred_vocabulary: string[];
    avoided_vocabulary: string[];
    signature_moves: string[];
    anti_patterns: string[];
    positive_examples: { label?: string; input: string; output: string }[];
    negative_examples: { label?: string; input: string; reason?: string }[];
  };
  content_preservation_rules: string[];
  transformation_rules: string[];
  body_markdown: string;
};

export type RewriteResult = {
  output: string;
  scores: {
    meaning_preservation: number;
    style_match: number;
    readability: number;
    platform_fit: number;
    final_score: number;
  };
  alternatives: string[];
};

export type ConfidenceReport = {
  overall: number;
  dimensions: Record<string, number>;
  warnings: string[];
};

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function listPersonas(params?: { category?: string; tag?: string; query?: string }) {
  const qs = new URLSearchParams();
  if (params?.category) qs.set("category", params.category);
  if (params?.tag) qs.set("tag", params.tag);
  if (params?.query) qs.set("query", params.query);
  return request<{ count: number; personas: Persona[] }>(`/v1/personas?${qs}`);
}

export function getPersona(id: string) {
  return request<Persona>(`/v1/personas/${id}`);
}

export function extractPersona(payload: { name?: string; samples: string[]; language?: string }) {
  return request<{
    persona_id: string;
    status: string;
    persona: Persona;
    confidence: ConfidenceReport;
  }>("/v1/personas/extract", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createPersona(persona: Persona) {
  return request<{ status: string; path: string }>("/v1/personas", {
    method: "POST",
    body: JSON.stringify({ persona }),
  });
}

export function rewrite(payload: {
  persona_id?: string;
  persona?: Persona;
  text: string;
  style_strength: number;
  platform?: string;
  preserve_length?: boolean;
  candidate_count?: number;
}) {
  return request<RewriteResult>("/v1/rewrite", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function mixPreview(personas: { id: string; weight: number }[]) {
  return request<Persona>("/v1/mix", {
    method: "POST",
    body: JSON.stringify({ personas }),
  });
}
