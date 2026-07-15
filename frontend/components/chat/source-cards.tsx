"use client";

import { FileText } from "lucide-react";

import type { Citation } from "@/types";

export function SourceCards({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;

  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-2">
      {citations.map((citation) => (
        <div
          key={citation.chunk_id}
          className="animate-fade-in rounded-lg border border-border bg-muted/40 p-3"
        >
          <div className="mb-1 flex items-center gap-2 text-sm font-medium">
            <FileText className="h-3.5 w-3.5 text-primary" />
            <span className="truncate">{citation.document_name}</span>
          </div>
          <p className="mb-1 text-xs text-muted-foreground">
            {citation.page != null ? `Page ${citation.page}` : "Page unavailable"} · score{" "}
            {citation.score.toFixed(2)}
          </p>
          <p className="line-clamp-3 text-xs leading-relaxed text-muted-foreground">
            {citation.excerpt}
          </p>
        </div>
      ))}
    </div>
  );
}
