"use client";

import { useRef, type WheelEvent } from "react";

const QUESTIONS = [
  "Give me my weekly briefing",
  "Which restaurants need immediate attention?",
  "What growth opportunities do I have?",
  "How should I spend my remaining budget?",
  "Show me my RESCUE restaurants",
];

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleWheel = (e: WheelEvent<HTMLDivElement>) => {
    const el = scrollRef.current;
    if (!el) return;
    // Translate vertical wheel into horizontal scroll when there's overflow.
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      el.scrollLeft += e.deltaY;
    }
  };

  return (
    <div
      ref={scrollRef}
      onWheel={handleWheel}
      className="overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
    >
      <div className="flex gap-2 w-max">
        {QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="shrink-0 border border-border bg-background rounded-lg px-4 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground cursor-pointer transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
