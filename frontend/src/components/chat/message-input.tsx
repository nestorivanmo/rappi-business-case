"use client";

import { useState, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask about your portfolio..."
        disabled={disabled}
        className="flex-1"
      />
      <Button type="submit" disabled={disabled || !value.trim()}>
        Send
      </Button>
    </form>
  );
}
