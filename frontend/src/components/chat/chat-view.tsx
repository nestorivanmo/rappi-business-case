"use client";

import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { Plus, Loader2 } from "lucide-react";
import { useChat } from "@/hooks/use-chat";
import { useDashboard } from "@/hooks/use-dashboard";
import { useActions } from "@/hooks/use-actions";
import { MessageList } from "./message-list";
import { ActionCard } from "./action-card";
import { DescriptivePanel } from "@/components/dashboard/descriptive-panel";
import { AnalyticalPanel } from "@/components/dashboard/analytical-panel";
import { SuggestedQuestions } from "./suggested-questions";

export function ChatView({ kam }: { kam: string }) {
  const { messages, sendMessage, isStreaming, clearMessages } = useChat(kam);
  const { overview, restaurants, isLoading } = useDashboard(kam);
  const { actions, createAction, removeAction, isCreating, error: actionsError } = useActions(kam);
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const firstName = kam.split(" ")[0];
  const hasMessages = messages.length > 0;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  }, [value]);

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    sendMessage(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleAddToAction = async () => {
    if (!hasMessages || isStreaming || isCreating) return;
    const ok = await createAction(messages);
    if (ok) clearMessages();
  };

  return (
    <div className="flex-1 flex min-h-0">
      {/* Left 1/4 — Descriptive data */}
      <div className="w-1/4 bg-white px-8 pt-8 overflow-y-auto">
        <h1 className="text-5xl font-bold text-foreground">
          Hello, <span className="text-rappi">{firstName}</span>
        </h1>
        <p className="mt-2 text-lg italic text-gray-400">
          Here are the latest data insights...
        </p>
        <div className="mt-8">
          <DescriptivePanel restaurants={restaurants} totalRevenue={overview?.total_revenue} isLoading={isLoading} />
        </div>
      </div>

      {/* Center 3/4 — Analytics + Chat + New section */}
      <div className="w-3/4 min-w-0 flex flex-col pt-8 min-h-0">
        {/* Analytical summary — spans full width */}
        <div className="w-full px-10">
          <div className="mb-[6vh]">
            <AnalyticalPanel overview={overview} isLoading={isLoading} />
          </div>
        </div>

        {/* Below analytics: chat area (2/3) | new section (1/3) */}
        <div className="flex flex-1 min-h-0">
          {/* Chat area — 2/3 */}
          <div className="flex-[2] min-w-0 px-10 flex flex-col min-h-0">
            <form onSubmit={handleSubmit} className="flex items-end gap-3 border-b-2 border-rappi pb-2">
              <textarea
                ref={textareaRef}
                rows={1}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={focused ? undefined : "What should we tackle next? Ask me anything"}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                disabled={isStreaming}
                className="flex-1 bg-transparent text-xl text-gray-400 text-left outline-none resize-none placeholder:text-gray-400 placeholder:italic disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isStreaming || !value.trim()}
                className="shrink-0 text-rappi hover:opacity-70 disabled:opacity-30 transition-opacity"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </button>
            </form>

            {/* Clear chat — below the bar, left-aligned */}
            {hasMessages && (
              <div className="mt-2">
                <button
                  onClick={clearMessages}
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  Clear chat
                </button>
              </div>
            )}

            {/* Suggested questions — hide when text is entered or messages exist */}
            {!hasMessages && !value && (
              <div className="pt-4">
                <SuggestedQuestions onSelect={(q) => { setValue(q); textareaRef.current?.focus(); }} />
              </div>
            )}

            {/* Messages area */}
            {hasMessages && (
              <div className="flex-1 min-h-0 overflow-hidden mt-4">
                <MessageList messages={messages} />
              </div>
            )}

            {/* Add to Action button — bottom of chat column, only when messages exist */}
            {hasMessages && (
              <div className="shrink-0 pt-3 pb-4 flex flex-col items-center gap-2">
                {actionsError && (
                  <p className="text-xs text-red-500">{actionsError}</p>
                )}
                <button
                  type="button"
                  onClick={handleAddToAction}
                  disabled={isStreaming || isCreating}
                  className="bg-rappi text-white text-sm font-medium px-5 py-2.5 rounded-full hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center gap-2"
                >
                  {isCreating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  {isCreating ? "Summarizing..." : "Add to Action"}
                </button>
              </div>
            )}
          </div>

          {/* Actions — 1/3, with vertical divider */}
          <div className="flex-1 min-w-0 border-l border-gray-200 px-10 flex flex-col min-h-0">
            <h2 className="text-2xl font-bold text-foreground shrink-0">Actions</h2>
            <div className="flex-1 overflow-y-auto mt-4 space-y-3 pb-4">
              {actions.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">
                  Your saved actions will appear here.
                </p>
              ) : (
                actions.map((action) => (
                  <ActionCard
                    key={action.id}
                    action={action}
                    onRemove={removeAction}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
