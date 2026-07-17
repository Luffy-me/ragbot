"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { ChatInput } from "@/components/chat/chat-input";
import { MessageList } from "@/components/chat/message-list";
import { AppShell } from "@/components/layout/app-shell";
import { useAuth } from "@/hooks/useAuth";
import * as api from "@/services/api";
import type { ChatMessage } from "@/types";

function ChatPageInner() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const historyQuery = useQuery({
    queryKey: ["chat-history", token],
    enabled: !!token,
    queryFn: () => api.fetchHistory(token!),
  });

  useEffect(() => {
    if (!historyQuery.data || messages.length > 0) return;
    const restored: ChatMessage[] = [];
    [...historyQuery.data].reverse().forEach((item) => {
      restored.push({
        id: `${item.id}-q`,
        role: "user",
        content: item.question,
        createdAt: item.created_at,
      });
      restored.push({
        id: `${item.id}-a`,
        role: "assistant",
        content: item.answer,
        citations: item.citations,
        createdAt: item.created_at,
      });
    });
    setMessages(restored);
  }, [historyQuery.data, messages.length]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const empty = useMemo(() => messages.length === 0 && !historyQuery.isLoading, [messages, historyQuery.isLoading]);

  async function handleSend(question: string) {
    if (!token) return;
    setError(null);
    const userMessage: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: question,
    };
    const assistantId = `a-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantId, role: "assistant", content: "", citations: [] },
    ]);
    setStreaming(true);
    setStatus("Connecting to knowledge base…");

    try {
      for await (const event of api.streamChat(token, question)) {
        if (event.type === "status") {
          setStatus(event.content);
        } else if (event.type === "citations") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, citations: event.citations } : m,
            ),
          );
        } else if (event.type === "token") {
          setStatus(null);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + event.content } : m,
            ),
          );
        } else if (event.type === "error") {
          throw new Error(event.content);
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to get answer";
      setError(message);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content:
                  m.content ||
                  "The assistant could not answer right now. Check that Docker services are running, then try again.",
              }
            : m,
        ),
      );
    } finally {
      setStreaming(false);
      setStatus(null);
    }
  }

  return (
    <AppShell>
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="border-b border-border px-4 py-4">
          <div className="mx-auto max-w-3xl">
            <h1 className="text-lg font-semibold">University Knowledge Chat</h1>
            <p className="text-sm text-muted-foreground">
              Answers are grounded in uploaded official documents and include citations.
            </p>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {empty && (
            <div className="mx-auto max-w-3xl px-4 py-16 text-center">
              <h2 className="mb-2 text-2xl font-semibold tracking-tight">Ask the knowledge base</h2>
              <p className="mx-auto max-w-lg text-sm text-muted-foreground">
                Try questions about applications, tuition, dormitories, visas, scholarships, or semester dates.
              </p>
            </div>
          )}
          <MessageList
            messages={messages}
            streaming={streaming && !messages.at(-1)?.content}
            status={status}
          />
          <div ref={bottomRef} />
        </div>

        {error && (
          <p className="mx-auto w-full max-w-3xl px-4 pb-2 text-sm text-destructive">{error}</p>
        )}
        <ChatInput onSend={handleSend} disabled={streaming} />
      </div>
    </AppShell>
  );
}

export default function ChatPage() {
  return (
    <AuthGate>
      <ChatPageInner />
    </AuthGate>
  );
}
