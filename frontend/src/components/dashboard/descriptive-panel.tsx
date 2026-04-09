"use client";

import type { RestaurantSummary } from "@/lib/types";
import { formatCurrency } from "@/lib/constants";
import { useMemo } from "react";

interface DescriptivePanelProps {
  restaurants?: RestaurantSummary[];
  totalRevenue?: number;
  isLoading?: boolean;
  onPrefill?: (prompt: string) => void;
}

export function DescriptivePanel({ restaurants, totalRevenue, isLoading, onPrefill }: DescriptivePanelProps) {
  const stats = useMemo(() => {
    if (!restaurants || restaurants.length === 0) return null;

    const vMap: Record<string, number> = {};
    const cMap: Record<string, number> = {};
    let ratingSum = 0;
    let deltaSum = 0;
    let ticketSum = 0;
    let cancelSum = 0;
    let deliverySum = 0;

    for (const r of restaurants) {
      vMap[r.vertical] = (vMap[r.vertical] || 0) + 1;
      cMap[r.ciudad] = (cMap[r.ciudad] || 0) + 1;
      ratingSum += r.rating_actual;
      deltaSum += r.delta_rating;
      ticketSum += r.valor_ticket_prom_mxn;
      cancelSum += r.tasa_cancelacion_pct;
      deliverySum += r.tiempo_entrega_avg_min;
    }

    const n = restaurants.length;
    return {
      totalCount: n,
      verticalCounts: Object.entries(vMap).sort((a, b) => b[1] - a[1]),
      cityCounts: Object.entries(cMap).sort((a, b) => b[1] - a[1]),
      avgRating: ratingSum / n,
      avgDelta: deltaSum / n,
      avgTicket: ticketSum / n,
      avgCancel: cancelSum / n,
      avgDelivery: deliverySum / n,
    };
  }, [restaurants]);

  if (isLoading || !stats) {
    return (
      <div className="space-y-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 bg-gray-200 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  const maxVertical = stats.verticalCounts[0]?.[1] || 1;
  const deltaPositive = stats.avgDelta >= 0;

  return (
    <div className="space-y-8">
      {/* Date range */}
      <button
        type="button"
        onClick={() => onPrefill?.("Walk me through what changed in my portfolio during the week of Apr 7, 2026 — wins, losses, and what needs attention.")}
        className="block w-full text-left rounded-md p-2 -m-2 cursor-pointer hover:bg-gray-50 transition-colors"
      >
        <span className="block text-xs font-medium text-muted-foreground uppercase tracking-wide">Data period</span>
        <span className="block text-base text-foreground mt-1">Week of Apr 7, 2026</span>
      </button>

      {/* KPI table */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">Portfolio metrics</p>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
        {/* Row 1: 3 columns */}
        <div className="grid grid-cols-3 divide-x divide-gray-200">
          <button
            type="button"
            onClick={() => onPrefill?.(`My portfolio has ${stats.totalCount} accounts. How is that book of business shaped, and where should I focus my time this week?`)}
            className="p-3 text-left cursor-pointer hover:bg-gray-100 transition-colors"
          >
            <span className="block text-xs font-medium text-gray-400 uppercase tracking-wide">Accounts</span>
            <span className="block text-2xl font-bold text-foreground mt-1">{stats.totalCount}</span>
          </button>
          <button
            type="button"
            onClick={() => onPrefill?.(`My portfolio's average rating is ${stats.avgRating.toFixed(1)} (${deltaPositive ? "up" : "down"} ${Math.abs(stats.avgDelta).toFixed(2)} WoW). Which restaurants are pulling this number, and what should I do about it?`)}
            className="p-3 text-left cursor-pointer hover:bg-gray-100 transition-colors"
          >
            <span className="block text-xs font-medium text-gray-400 uppercase tracking-wide">Avg. rating</span>
            <span className="flex items-baseline gap-1 mt-1">
              <span className="text-2xl font-bold text-foreground">{stats.avgRating.toFixed(1)}</span>
              <span className={`flex items-center text-xs font-semibold ${deltaPositive ? "text-green-600" : "text-red-500"}`}>
                {deltaPositive ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m18 15-6-6-6 6"/></svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                )}
                {Math.abs(stats.avgDelta).toFixed(2)}
              </span>
            </span>
          </button>
          <button
            type="button"
            onClick={() => onPrefill?.(`Average delivery time across my portfolio is ${Math.round(stats.avgDelivery)} min. Which restaurants are dragging this up and what's the recommended fix?`)}
            className="p-3 text-left cursor-pointer hover:bg-gray-100 transition-colors"
          >
            <span className="block text-xs font-medium text-gray-400 uppercase tracking-wide">Avg. delivery</span>
            <span className={`block text-2xl font-bold mt-1 ${stats.avgDelivery > 50 ? "text-red-500" : "text-foreground"}`}>
              {Math.round(stats.avgDelivery)} min
            </span>
          </button>
        </div>
        {/* Row 2: 3 columns */}
        <div className="grid grid-cols-3 divide-x divide-gray-200 border-t border-gray-200">
          <button
            type="button"
            onClick={() => onPrefill?.(`My portfolio's average cancellation rate is ${stats.avgCancel.toFixed(1)}%. Where is the bleeding coming from and how should I address it?`)}
            className="p-3 text-left cursor-pointer hover:bg-gray-100 transition-colors"
          >
            <span className="block text-xs font-medium text-gray-400 uppercase tracking-wide">Avg. cancel</span>
            <span className={`block text-2xl font-bold mt-1 ${stats.avgCancel > 15 ? "text-red-500" : "text-foreground"}`}>
              {stats.avgCancel.toFixed(1)}%
            </span>
          </button>
          <button
            type="button"
            onClick={() => onPrefill?.(`Average ticket value is ${formatCurrency(stats.avgTicket)}. Which restaurants are above and below the line, and where's the upside?`)}
            className="p-3 text-left cursor-pointer hover:bg-gray-100 transition-colors"
          >
            <span className="block text-xs font-medium text-gray-400 uppercase tracking-wide">Avg. ticket</span>
            <span className="block text-2xl font-bold text-foreground mt-1">{formatCurrency(stats.avgTicket)}</span>
          </button>
          {totalRevenue != null && (
            <button
              type="button"
              onClick={() => onPrefill?.(`My portfolio is generating ${formatCurrency(totalRevenue)} in weekly revenue. How is it distributed and what's the concentration risk?`)}
              className="p-3 min-w-0 text-left cursor-pointer hover:bg-gray-100 transition-colors"
            >
              <span className="block text-xs font-medium text-gray-400 uppercase tracking-wide">Revenue</span>
              <span className="block text-lg font-bold text-foreground mt-1 truncate">{formatCurrency(totalRevenue)}</span>
            </button>
          )}
        </div>
        </div>
      </div>

      {/* Vertical distribution — horizontal bar chart */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">By vertical</p>
        <div className="space-y-3">
          {stats.verticalCounts.map(([vertical, count]) => (
            <button
              key={vertical}
              type="button"
              onClick={() => onPrefill?.(`Let's talk about my ${count} restaurants in the ${vertical} vertical — how are they performing and where should I focus?`)}
              className="block w-full text-left rounded-md p-1.5 -mx-1.5 cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <span className="flex items-center justify-between text-sm mb-1">
                <span className="text-foreground font-medium">{vertical}</span>
                <span className="text-muted-foreground font-semibold">{count}</span>
              </span>
              <span className="block h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <span
                  className="block h-full bg-gray-400 rounded-full transition-all"
                  style={{ width: `${(count / maxVertical) * 100}%` }}
                />
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* City breakdown */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">By city</p>
        <div className="space-y-2.5">
          {stats.cityCounts.map(([city, count]) => (
            <button
              key={city}
              type="button"
              onClick={() => onPrefill?.(`Let's talk about my ${count} restaurants in ${city} — how does this market look and what should I prioritize?`)}
              className="flex w-full items-center justify-between text-base rounded-md px-2 py-1 -mx-2 cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <span className="text-foreground">{city}</span>
              <span className="text-muted-foreground font-semibold">{count}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
