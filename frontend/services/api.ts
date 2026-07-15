import { apiFetch, getApiUrl } from "@/lib/api";
import type {
  AuthResponse,
  ChatHistoryItem,
  Citation,
  DocumentItem,
  User,
} from "@/types";

export async function login(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(token: string): Promise<void> {
  await apiFetch("/auth/logout", { method: "POST" }, token);
}

export async function fetchMe(token: string): Promise<User> {
  return apiFetch<User>("/auth/me", {}, token);
}

export async function fetchHistory(token: string): Promise<ChatHistoryItem[]> {
  return apiFetch<ChatHistoryItem[]>("/chat/history", {}, token);
}

export async function chatOnce(
  token: string,
  question: string,
): Promise<{ answer: string; citations: Citation[]; conversation_id?: string }> {
  return apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify({ question, stream: false }),
  }, token);
}

export async function* streamChat(
  token: string,
  question: string,
): AsyncGenerator<
  | { type: "status"; content: string }
  | { type: "citations"; citations: Citation[] }
  | { type: "token"; content: string }
  | { type: "error"; content: string }
  | { type: "done"; conversation_id: string }
> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180_000);

  try {
    const response = await fetch(`${getApiUrl()}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ question, stream: true }),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) {
      let detail = "Chat request failed";
      try {
        const data = await response.json();
        detail = data.detail || detail;
      } catch {
        // ignore
      }
      throw new Error(detail);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload) continue;
        yield JSON.parse(payload);
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Chat timed out. Check that Docker, the backend, and Ollama are running.",
      );
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function listDocuments(token: string): Promise<DocumentItem[]> {
  return apiFetch<DocumentItem[]>("/documents", {}, token);
}

export async function uploadDocument(token: string, file: File): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<DocumentItem>(
    "/documents/upload",
    { method: "POST", body: form },
    token,
  );
}

export async function deleteDocument(token: string, id: string): Promise<void> {
  await apiFetch(`/documents/${id}`, { method: "DELETE" }, token);
}

export async function reindexDocuments(token: string): Promise<{ message: string }> {
  return apiFetch("/documents/reindex", { method: "POST" }, token);
}
