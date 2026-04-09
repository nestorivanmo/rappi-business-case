"use client";

import type { ChatMessage } from "@/lib/types";
import { useEffect, useRef } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const markdownComponents: Components = {
  p: ({ children }) => <p className="my-2">{children}</p>,
  ul: ({ children }) => <ul className="list-disc ml-5 my-2">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal ml-5 my-2">{children}</ol>,
  li: ({ children }) => <li className="my-0.5">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  code: ({ children, className }) => {
    // Block code is wrapped in <pre><code>; inline code has no language class
    const isBlock = (className ?? "").startsWith("language-");
    if (isBlock) {
      return <code className={className}>{children}</code>;
    }
    return (
      <code className="bg-gray-100 px-1 rounded text-[0.85em] font-mono">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="bg-gray-100 rounded-lg p-3 overflow-x-auto my-2 text-xs">
      {children}
    </pre>
  ),
  a: ({ href, children }) => (
    <a href={href} className="text-rappi underline" target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
  h1: ({ children }) => (
    <h1 className="text-lg font-semibold mt-3 mb-1">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-base font-semibold mt-3 mb-1">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-semibold mt-3 mb-1">{children}</h3>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-gray-300 pl-3 italic text-gray-600 my-2">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <table className="border-collapse my-2">{children}</table>
  ),
  th: ({ children }) => (
    <th className="border border-gray-200 px-2 py-1 font-semibold">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border border-gray-200 px-2 py-1">{children}</td>
  ),
};

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="h-full overflow-y-auto px-6 py-4 [scrollbar-width:thin] [scrollbar-color:theme(colors.gray.300)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-gray-400">
      <div className="max-w-2xl mx-auto space-y-4">
        {messages.map((msg, i) => {
          if (msg.role === "user") {
            return (
              <div key={i} className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl px-4 py-2.5 text-base whitespace-pre-wrap bg-rappi text-white">
                  {msg.content}
                </div>
              </div>
            );
          }

          // Assistant: no bubble, free-flowing markdown
          return (
            <div key={i} className="flex justify-start">
              <div className="max-w-[85%] text-base text-gray-900 leading-relaxed">
                {msg.content ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={markdownComponents}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  <span className="animate-pulse text-muted-foreground">
                    Thinking...
                  </span>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
