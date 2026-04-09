"use client";

import { useState, useCallback, useEffect } from "react";
import { summarizeChat } from "@/lib/api";
import type { Action, ChatMessage } from "@/lib/types";

export function useActions(kam: string) {
  const [actions, setActions] = useState<Action[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createAction = useCallback(
    async (messages: ChatMessage[]): Promise<boolean> => {
      if (messages.length === 0) return false;
      setIsCreating(true);
      setError(null);
      try {
        const { title, summary } = await summarizeChat(kam, messages);
        setActions((prev) => [
          {
            id: crypto.randomUUID(),
            title,
            summary,
            createdAt: new Date().toISOString(),
            messageCount: messages.length,
          },
          ...prev,
        ]);
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to create action");
        return false;
      } finally {
        setIsCreating(false);
      }
    },
    [kam]
  );

  const removeAction = useCallback((id: string) => {
    setActions((prev) => prev.filter((a) => a.id !== id));
  }, []);

  // Reset on KAM switch (safety net in case ChatView doesn't remount)
  useEffect(() => {
    setActions([]);
    setError(null);
  }, [kam]);

  return { actions, createAction, removeAction, isCreating, error };
}
