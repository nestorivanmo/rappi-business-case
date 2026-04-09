"use client";

import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchRestaurants } from "@/lib/api";
import { QUADRANT_COLORS, formatCurrency } from "@/lib/constants";
import type { RestaurantSummary } from "@/lib/types";

const QUADRANT_TABS = ["ALL", "GROW", "RESCUE", "NURTURE", "TRIAGE"] as const;

export function RestaurantTable({ kam }: { kam: string }) {
  const [restaurants, setRestaurants] = useState<RestaurantSummary[]>([]);
  const [activeTab, setActiveTab] = useState<string>("ALL");

  useEffect(() => {
    fetchRestaurants(kam).then(setRestaurants);
  }, [kam]);

  const filtered =
    activeTab === "ALL"
      ? restaurants
      : restaurants.filter((r) => r.quadrant === activeTab);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Restaurants</CardTitle>
        <div className="flex gap-1 mt-2">
          {QUADRANT_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                activeTab === tab
                  ? "bg-orange-100 text-orange-800 font-medium"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {tab}{" "}
              {tab === "ALL"
                ? `(${restaurants.length})`
                : `(${restaurants.filter((r) => r.quadrant === tab).length})`}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="max-h-[400px] overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Health</TableHead>
                <TableHead>Quadrant</TableHead>
                <TableHead className="text-right">Revenue</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow key={r.restaurant_id}>
                  <TableCell className="font-medium text-sm">
                    {r.nombre}
                    {r.velocity_flag && (
                      <span className="ml-1 text-orange-500" title="Velocity alert">
                        ⚡
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {r.ciudad}
                  </TableCell>
                  <TableCell>
                    <span
                      className={`text-sm font-medium ${
                        r.health_score >= 60
                          ? "text-green-600"
                          : r.health_score >= 40
                          ? "text-yellow-600"
                          : "text-red-600"
                      }`}
                    >
                      {r.health_score.toFixed(1)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge
                      style={{
                        backgroundColor: `${QUADRANT_COLORS[r.quadrant]}20`,
                        color: QUADRANT_COLORS[r.quadrant],
                      }}
                      className="text-xs"
                    >
                      {r.quadrant}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-sm">
                    {formatCurrency(r.weekly_revenue)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
