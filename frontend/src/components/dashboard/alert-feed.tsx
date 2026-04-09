"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatCurrency, SIGNAL_LABELS } from "@/lib/constants";
import type { RestaurantSummary } from "@/lib/types";

export function AlertFeed({ alerts }: { alerts?: RestaurantSummary[] }) {
  if (!alerts || alerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Velocity Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No active alerts</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Velocity Alerts ({alerts.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.restaurant_id}
                className="border rounded-lg p-3 space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{alert.nombre}</span>
                  <Badge
                    variant={
                      alert.escalation_level === "immediate"
                        ? "destructive"
                        : "secondary"
                    }
                    className="text-xs"
                  >
                    {alert.escalation_level === "immediate"
                      ? "IMMEDIATE"
                      : "5 DAY"}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{alert.ciudad}</span>
                  <span>·</span>
                  <span>{alert.vertical}</span>
                  <span>·</span>
                  <span>Health: {alert.health_score.toFixed(1)}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-muted-foreground">
                    {formatCurrency(alert.weekly_revenue)}/week
                  </span>
                  <span>·</span>
                  <span className="text-orange-600">
                    {alert.dominant_risk_signals
                      .map((s) => SIGNAL_LABELS[s] || s)
                      .join(", ")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
