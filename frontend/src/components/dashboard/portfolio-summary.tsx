"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/constants";
import type { PortfolioOverview } from "@/lib/types";

export function PortfolioSummary({ overview }: { overview?: PortfolioOverview }) {
  if (!overview) return null;

  const cards = [
    {
      title: "Restaurants",
      value: overview.total_restaurants,
      detail: (
        <div className="flex gap-1 flex-wrap mt-1">
          <Badge className="bg-green-100 text-green-800 text-xs">
            {overview.quadrant_distribution.GROW} Grow
          </Badge>
          <Badge className="bg-red-100 text-red-800 text-xs">
            {overview.quadrant_distribution.RESCUE} Rescue
          </Badge>
          <Badge className="bg-blue-100 text-blue-800 text-xs">
            {overview.quadrant_distribution.NURTURE} Nurture
          </Badge>
          <Badge className="bg-gray-100 text-gray-800 text-xs">
            {overview.quadrant_distribution.TRIAGE} Triage
          </Badge>
        </div>
      ),
    },
    {
      title: "Weekly Revenue",
      value: formatCurrency(overview.total_revenue),
      detail: null,
    },
    {
      title: "Revenue at Risk",
      value: formatCurrency(overview.revenue_at_risk),
      detail: (
        <span className="text-xs text-muted-foreground">RESCUE + TRIAGE</span>
      ),
    },
    {
      title: "Velocity Alerts",
      value: overview.velocity_alert_count,
      detail: overview.velocity_alert_count > 0 ? (
        <span className="text-xs text-orange-600">Needs attention</span>
      ) : (
        <span className="text-xs text-green-600">All clear</span>
      ),
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {card.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            {card.detail}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
