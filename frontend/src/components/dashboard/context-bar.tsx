"use client";

import type { PortfolioOverview, BudgetBalance } from "@/lib/types";
import { formatCurrency, QUADRANT_COLORS } from "@/lib/constants";

interface ContextBarProps {
  overview?: PortfolioOverview;
  budget?: BudgetBalance;
  isLoading?: boolean;
}

const QUADRANTS = ["GROW", "RESCUE", "NURTURE", "TRIAGE"] as const;

export function ContextBar({ overview, budget, isLoading }: ContextBarProps) {
  if (isLoading || !overview) {
    return (
      <div className="max-w-[40vw] mx-auto flex items-center justify-center gap-6 py-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  const alertCount = overview.velocity_alert_count;

  return (
    <div className="max-w-[40vw] mx-auto flex items-center justify-center gap-5 py-4 text-sm">
      {/* Velocity Alerts */}
      <div className="flex items-center gap-1.5">
        <span
          className={`font-semibold ${
            alertCount === 0 ? "text-green-600" : "text-rappi"
          }`}
        >
          {alertCount}
        </span>
        <span className="text-muted-foreground">alerts</span>
      </div>

      <span className="text-gray-300">·</span>

      {/* Revenue at Risk */}
      <div className="flex items-center gap-1.5">
        <span className="font-semibold text-foreground">
          {formatCurrency(overview.revenue_at_risk)}
        </span>
        <span className="text-muted-foreground">at risk</span>
      </div>

      <span className="text-gray-300">·</span>

      {/* Quadrant Distribution */}
      <div className="flex items-center gap-2">
        {QUADRANTS.map((q) => (
          <div key={q} className="flex items-center gap-1">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: QUADRANT_COLORS[q] }}
            />
            <span className="font-semibold text-foreground text-xs">
              {overview.quadrant_distribution[q]}
            </span>
          </div>
        ))}
      </div>

      <span className="text-gray-300">·</span>

      {/* Budget Left */}
      <div className="flex items-center gap-1.5">
        <span className="font-semibold text-foreground">
          {budget ? formatCurrency(budget.remaining) : "—"}
        </span>
        <span className="text-muted-foreground">left</span>
      </div>
    </div>
  );
}
