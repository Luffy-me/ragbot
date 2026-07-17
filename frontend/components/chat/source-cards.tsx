"use client";

import type { Citation } from "@/types";

function formatReference(citation: Citation): string {
  if (citation.page != null) {
    return `${citation.document_name}, page ${citation.page}`;
  }
  return citation.document_name;
}

export function SourceCards({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;

  // Deduplicate by document + page so the list stays clean.
  const unique = Array.from(
    new Map(
      citations.map((citation) => [
        `${citation.document_name}::${citation.page ?? "na"}`,
        citation,
      ]),
    ).values(),
  );

  return (
    <div className="mt-3 border-t border-border/70 pt-2 text-xs text-muted-foreground">
      <p className="mb-1 font-medium text-foreground/80">Sources</p>
      <ul className="space-y-0.5">
        {unique.map((citation) => (
          <li key={citation.chunk_id}>{formatReference(citation)}</li>
        ))}
      </ul>
    </div>
  );
}
