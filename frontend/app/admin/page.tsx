"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { AuthGate } from "@/components/auth-gate";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { formatBytes, formatDate } from "@/lib/utils";
import * as api from "@/services/api";

function AdminPageInner() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents", token],
    enabled: !!token,
    queryFn: () => api.listDocuments(token!),
    refetchInterval: 5000,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadDocument(token!, file),
    onSuccess: () => {
      setMessage("Upload started. Indexing runs in the background.");
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: Error) => {
      setError(err.message);
      setMessage(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteDocument(token!, id),
    onSuccess: () => {
      setMessage("Document deleted.");
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const reindexMutation = useMutation({
    mutationFn: () => api.reindexDocuments(token!),
    onSuccess: (data) => {
      setMessage(data.message);
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-5xl space-y-6 px-4 py-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold">Knowledge Base Admin</h1>
            <p className="text-sm text-muted-foreground">
              Upload official PDFs, monitor indexing, and rebuild the vector store.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) uploadMutation.mutate(file);
                e.target.value = "";
              }}
            />
            <Button onClick={() => inputRef.current?.click()} disabled={uploadMutation.isPending}>
              <Upload className="h-4 w-4" />
              Upload PDF
            </Button>
            <Button
              variant="outline"
              onClick={() => reindexMutation.mutate()}
              disabled={reindexMutation.isPending}
            >
              <RefreshCw className="h-4 w-4" />
              Re-index
            </Button>
          </div>
        </div>

        {message && <p className="text-sm text-primary">{message}</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="overflow-hidden rounded-xl border border-border bg-card">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50 text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Document</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="hidden px-4 py-3 font-medium md:table-cell">Pages</th>
                <th className="hidden px-4 py-3 font-medium md:table-cell">Chunks</th>
                <th className="hidden px-4 py-3 font-medium lg:table-cell">Uploaded</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(documentsQuery.data || []).map((doc) => (
                <tr key={doc.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3">
                    <div className="font-medium">{doc.filename}</div>
                    <div className="text-xs text-muted-foreground">{formatBytes(doc.file_size)}</div>
                    {doc.error_message && (
                      <div className="mt-1 text-xs text-destructive">{doc.error_message}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Badge
                      className={
                        doc.status === "ready"
                          ? "border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                          : doc.status === "failed"
                            ? "border-destructive/30 text-destructive"
                            : ""
                      }
                    >
                      {doc.status}
                    </Badge>
                  </td>
                  <td className="hidden px-4 py-3 md:table-cell">{doc.page_count}</td>
                  <td className="hidden px-4 py-3 md:table-cell">{doc.chunk_count}</td>
                  <td className="hidden px-4 py-3 lg:table-cell">{formatDate(doc.uploaded_at)}</td>
                  <td className="px-4 py-3">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteMutation.mutate(doc.id)}
                      disabled={deleteMutation.isPending}
                      aria-label={`Delete ${doc.filename}`}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </td>
                </tr>
              ))}
              {!documentsQuery.isLoading && (documentsQuery.data || []).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">
                    No documents uploaded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}

export default function AdminPage() {
  return (
    <AuthGate adminOnly>
      <AdminPageInner />
    </AuthGate>
  );
}
