"use client";

import { X } from "lucide-react";
import type { Action } from "@/lib/types";

interface ActionCardProps {
  action: Action;
  onRemove: (id: string) => void;
}

export function ActionCard({ action, onRemove }: ActionCardProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-foreground leading-snug">
          {action.title}
        </h3>
        <button
          onClick={() => onRemove(action.id)}
          aria-label="Remove action"
          className="shrink-0 text-gray-300 hover:text-rappi transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <p className="mt-2 text-xs text-gray-600 leading-relaxed">
        {action.summary}
      </p>
      <p className="mt-3 text-[10px] uppercase tracking-wide text-gray-400">
        {new Date(action.createdAt).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </p>
    </div>
  );
}
