"use client";

import { SendHorizonal } from "lucide-react";
import { FormEvent, KeyboardEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (value: string) => Promise<void> | void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");

  async function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    setValue("");
    await onSend(trimmed);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit();
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="mx-auto flex w-full max-w-3xl items-end gap-2 border-t border-border bg-background/90 px-4 py-4 backdrop-blur"
    >
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Ask about admissions, tuition, visas, housing…"
        className="min-h-[52px] max-h-40 resize-none"
        disabled={disabled}
      />
      <Button type="submit" size="icon" className="h-[52px] w-[52px]" disabled={disabled || !value.trim()}>
        <SendHorizonal className="h-4 w-4" />
      </Button>
    </form>
  );
}
