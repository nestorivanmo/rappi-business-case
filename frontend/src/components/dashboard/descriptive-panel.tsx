"use client";

import type { RestaurantSummary } from "@/lib/types";
import { formatCurrency } from "@/lib/constants";
import { useMemo } from "react";

interface DescriptivePanelProps {
  restaurants?: RestaurantSummary[];
  totalRevenue?: number;
  isLoading?: boolean;
}

export function DescriptivePanel({ restaurants, totalRevenue, isLoading }: DescriptivePanelProps) {
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
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Data period</p>
        <p className="text-base text-foreground mt-1">Week of Apr 7, 2026</p>
      </div>

      {/* KPI table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        {/* Row 1: 3 columns */}
        <div className="grid grid-cols-3 divide-x divide-gray-200">
          <div className="p-3">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Accounts</p>
            <p className="text-2xl font-bold text-foreground mt-1">{stats.totalCount}</p>
          </div>
          <div className="p-3">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Avg. rating</p>
            <div className="flex items-baseline gap-1 mt-1">
              <p className="text-2xl font-bold text-foreground">{stats.avgRating.toFixed(1)}</p>
              <span className={`flex items-center text-xs font-semibold ${deltaPositive ? "text-green-600" : "text-red-500"}`}>
                {deltaPositive ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m18 15-6-6-6 6"/></svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                )}
                {Math.abs(stats.avgDelta).toFixed(2)}
              </span>
            </div>
          </div>
          <div className="p-3">
            <p className={`text-xs font-medium text-gray-400 uppercase tracking-wide`}>Avg. delivery</p>
            <p className={`text-2xl font-bold text-foreground mt-1 ${stats.avgDelivery > 50 ? "text-red-500" : "text-foreground"}`}>
              {Math.round(stats.avgDelivery)} min
            </p>
          </div>
        </div>
        {/* Row 2: 3 columns */}
        <div className="grid grid-cols-3 divide-x divide-gray-200 border-t border-gray-200">
          <div className="p-3">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Avg. cancel</p>
            <p className={`text-2xl font-bold mt-1 ${stats.avgCancel > 15 ? "text-red-500" : "text-foreground"}`}>
              {stats.avgCancel.toFixed(1)}%
            </p>
          </div>
          <div className="p-3">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Avg. ticket</p>
            <p className="text-2xl font-bold text-foreground mt-1">{formatCurrency(stats.avgTicket)}</p>
          </div>
          {totalRevenue != null && (
            <div className="p-3 min-w-0">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Revenue</p>
              <p className="text-lg font-bold text-foreground mt-1 truncate">{formatCurrency(totalRevenue)}</p>
            </div>
          )}
        </div>
      </div>

      {/* Vertical distribution — horizontal bar chart */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">By vertical</p>
        <div className="space-y-3">
          {stats.verticalCounts.map(([vertical, count]) => (
            <div key={vertical}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-foreground font-medium">{vertical}</span>
                <span className="text-muted-foreground font-semibold">{count}</span>
              </div>
              <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gray-400 rounded-full transition-all"
                  style={{ width: `${(count / maxVertical) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* City breakdown */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">By city</p>
        <div className="space-y-2.5">
          {stats.cityCounts.map(([city, count]) => (
            <div key={city} className="flex items-center justify-between text-base">
              <span className="text-foreground">{city}</span>
              <span className="text-muted-foreground font-semibold">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
