export type UserRole = "student" | "admin";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page: number | null;
  chunk_id: string;
  excerpt: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  createdAt?: string;
}

export interface ChatHistoryItem {
  id: string;
  question: string;
  answer: string;
  citations: Citation[];
  created_at: string;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_size: number;
  status: "pending" | "indexing" | "ready" | "failed" | string;
  error_message?: string | null;
  page_count: number;
  chunk_count: number;
  uploaded_at: string;
  indexed_at?: string | null;
}
