"use client";

import { useState, useCallback } from "react";
import { streamChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export function useChat(kam: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = { role: "user", content };
      const updatedMessages = [...messages, userMsg];
      setMessages([...updatedMessages, { role: "assistant", content: "" }]);
      setIsStreaming(true);

      try {
        let assistantContent = "";
        for await (const chunk of streamChat(kam, updatedMessages)) {
          assistantContent += chunk;
          setMessages([
            ...updatedMessages,
            { role: "assistant", content: assistantContent },
          ]);
        }
      } catch (error) {
        const detail =
          error instanceof Error && error.message
            ? error.message
            : "unknown error";
        setMessages([
          ...updatedMessages,
          {
            role: "assistant",
            content: `The agent hit an error and could not finish: ${detail}. Please try again.`,
          },
        ]);
      } finally {
        setIsStreaming(false);
      }
    },
    [messages, kam]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, sendMessage, isStreaming, clearMessages };
}
