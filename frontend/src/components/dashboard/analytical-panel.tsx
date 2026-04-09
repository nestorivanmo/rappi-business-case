"use client";

import { useState } from "react";
import type { PortfolioOverview } from "@/lib/types";
import { formatCurrency } from "@/lib/constants";

interface AnalyticalPanelProps {
  overview?: PortfolioOverview;
  isLoading?: boolean;
  compact?: boolean;
}

type Direction = "up" | "down";

interface QuadrantMeta {
  label: string;
  tooltip: string;
  bg: string;
  text: string;
  number: string;
  health: Direction;
  value: Direction;
}

const QUADRANT_META: Record<string, QuadrantMeta> = {
  GROW: {
    label: "Grow",
    tooltip: "High health, high value — protect and expand. These are the portfolio's revenue engine.",
    bg: "bg-green-50",
    text: "text-green-700",
    number: "text-green-600",
    health: "up",
    value: "up",
  },
  RESCUE: {
    label: "Rescue",
    tooltip: "Low health, high value — stop the bleeding. High revenue at stake, deteriorating health. Act today.",
    bg: "bg-red-50",
    text: "text-red-700",
    number: "text-red-600",
    health: "down",
    value: "up",
  },
  NURTURE: {
    label: "Nurture",
    tooltip: "High health, low value — stable but small. Help them scale into high-value territory.",
    bg: "bg-blue-50",
    text: "text-blue-700",
    number: "text-blue-600",
    health: "up",
    value: "down",
  },
  TRIAGE: {
    label: "Triage",
    tooltip: "Low health, low value — evaluate whether recovery is worth the investment.",
    bg: "bg-gray-100",
    text: "text-gray-700",
    number: "text-gray-600",
    health: "down",
    value: "down",
  },
};

function DirectionArrow({ direction }: { direction: Direction }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {direction === "up" ? (
        <>
          <path d="M12 19V5" />
          <path d="m5 12 7-7 7 7" />
        </>
      ) : (
        <>
          <path d="M12 5v14" />
          <path d="m19 12-7 7-7-7" />
        </>
      )}
    </svg>
  );
}

export function AnalyticalPanel({ overview, isLoading, compact = false }: AnalyticalPanelProps) {
  const [showGmvTooltip, setShowGmvTooltip] = useState(false);
  const [activeQuadrantTooltip, setActiveQuadrantTooltip] = useState<string | null>(null);

  if (isLoading || !overview) {
    return (
      <div className="flex gap-6">
        <div className="h-20 flex-1 bg-gray-200 rounded animate-pulse" />
        <div className="h-20 flex-[2] bg-gray-200 rounded animate-pulse" />
      </div>
    );
  }

  const dist = overview.quadrant_distribution;

  const cardPadding = compact ? "p-3" : "p-5";
  const gmvValueSize = compact ? "text-2xl" : "text-4xl";
  const gmvPctSize = compact ? "text-sm" : "text-base";
  const quadrantNumberSize = compact ? "text-2xl" : "text-4xl";
  const quadrantLabelSize = compact ? "text-xs" : "text-sm";

  return (
    <div className="grid grid-cols-6 gap-3">
      {/* GMV at stake — spans 2 columns */}
      <div className={`relative col-span-2 rounded-2xl bg-gray-50 ${cardPadding}`}>
        <div className="inline-flex items-center gap-1.5">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">GMV at stake</p>
          <button
            type="button"
            onMouseEnter={() => setShowGmvTooltip(true)}
            onMouseLeave={() => setShowGmvTooltip(false)}
            onClick={() => setShowGmvTooltip((v) => !v)}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
          </button>
        </div>
        {showGmvTooltip && (
          <div className="absolute left-5 top-12 z-10 w-64 rounded-lg border bg-white p-3 shadow-md text-xs text-muted-foreground leading-relaxed text-left">
            Sum of <span className="font-semibold text-foreground">ordenes_7d × valor_ticket_prom</span> for
            RESCUE and TRIAGE restaurants — weekly revenue at risk without intervention.
          </div>
        )}
        <div className="flex items-baseline gap-2 mt-2">
          <p className={`${gmvValueSize} font-bold text-rappi`}>{formatCurrency(overview.revenue_at_risk)}</p>
          <span className={`${gmvPctSize} font-semibold text-muted-foreground whitespace-nowrap`}>
            {overview.total_revenue > 0
              ? `${((overview.revenue_at_risk / overview.total_revenue) * 100).toFixed(1)}%`
              : "—"}
          </span>
        </div>
      </div>

      {/* Health quadrants — 4 individual cards */}
      {(["GROW", "RESCUE", "NURTURE", "TRIAGE"] as const).map((q) => {
        const meta = QUADRANT_META[q];
        return (
          <div key={q} className={`relative rounded-2xl ${meta.bg} ${cardPadding} flex flex-col items-center justify-center`}>
            <p className={`${quadrantNumberSize} font-bold ${meta.number}`}>{dist[q]}</p>
            <div className="flex items-center gap-1.5 mt-1">
              <span className={`${quadrantLabelSize} font-medium ${meta.text}`}>{meta.label}</span>
              <button
                type="button"
                onMouseEnter={() => setActiveQuadrantTooltip(q)}
                onMouseLeave={() => setActiveQuadrantTooltip(null)}
                onClick={() => setActiveQuadrantTooltip((v) => v === q ? null : q)}
                className={`${meta.text} opacity-50 hover:opacity-100 transition-opacity`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 16v-4" />
                  <path d="M12 8h.01" />
                </svg>
              </button>
            </div>
            <div className={`flex items-center gap-1.5 mt-1 text-[11px] font-medium ${meta.text}`}>
              <span className="flex items-center gap-0.5">
                <DirectionArrow direction={meta.health} />
                Health
              </span>
              <span className="opacity-40">|</span>
              <span className="flex items-center gap-0.5">
                <DirectionArrow direction={meta.value} />
                Value
              </span>
            </div>
            {activeQuadrantTooltip === q && (
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 z-10 w-56 rounded-lg border bg-white p-3 shadow-md text-xs text-muted-foreground leading-relaxed text-left">
                {meta.tooltip}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
