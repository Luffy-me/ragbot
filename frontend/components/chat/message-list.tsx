"use client";

import { SourceCards } from "@/components/chat/source-cards";
import type { ChatMessage } from "@/types";
import { cn } from "@/lib/utils";

export function MessageList({
  messages,
  streaming,
}: {
  messages: ChatMessage[];
  streaming?: boolean;
}) {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={cn(
            "animate-fade-in rounded-2xl px-4 py-3 text-sm leading-relaxed",
            message.role === "user"
              ? "ml-auto max-w-[85%] bg-primary text-primary-foreground"
              : "mr-auto max-w-[95%] border border-border bg-card",
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
          {message.role === "assistant" && message.citations && (
            <SourceCards citations={message.citations} />
          )}
        </div>
      ))}
      {streaming && (
        <div className="mr-auto flex items-center gap-1 rounded-2xl border border-border bg-card px-4 py-3 text-sm text-muted-foreground">
          <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary" />
          <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary [animation-delay:300ms]" />
        </div>
      )}
    </div>
  );
}
