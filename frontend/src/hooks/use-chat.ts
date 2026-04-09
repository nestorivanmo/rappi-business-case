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
        setMessages([
          ...updatedMessages,
          {
            role: "assistant",
            content: "Error connecting to the agent. Please try again.",
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
