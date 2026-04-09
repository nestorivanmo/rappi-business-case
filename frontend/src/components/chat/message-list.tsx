"use client";

import type { ChatMessage } from "@/lib/types";
import { useEffect, useRef } from "react";

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      <div className="max-w-2xl mx-auto space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-rappi text-white"
                  : "bg-white border border-gray-200 text-gray-900"
              }`}
            >
              {msg.content || (
                <span className="animate-pulse text-muted-foreground">
                  Thinking...
                </span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
