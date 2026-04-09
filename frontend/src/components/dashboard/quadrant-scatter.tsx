"use client";

import { useEffect, useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchRestaurants } from "@/lib/api";
import { QUADRANT_COLORS, formatCurrency } from "@/lib/constants";
import type { RestaurantSummary } from "@/lib/types";

interface ScatterPoint {
  x: number;
  y: number;
  nombre: string;
  quadrant: string;
  restaurant_id: string;
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.[0]) return null;
  const data = payload[0].payload as ScatterPoint;
  return (
    <div className="bg-white border rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold">{data.nombre}</p>
      <p>Health: {data.x.toFixed(1)}</p>
      <p>Revenue: {formatCurrency(data.y)}</p>
      <p className="capitalize">{data.quadrant}</p>
    </div>
  );
}

export function QuadrantScatter({ kam }: { kam: string }) {
  const [data, setData] = useState<Record<string, ScatterPoint[]>>({});

  useEffect(() => {
    fetchRestaurants(kam).then((restaurants: RestaurantSummary[]) => {
      const grouped: Record<string, ScatterPoint[]> = {
        GROW: [],
        RESCUE: [],
        NURTURE: [],
        TRIAGE: [],
      };
      for (const r of restaurants) {
        const point: ScatterPoint = {
          x: r.health_score,
          y: r.weekly_revenue,
          nombre: r.nombre,
          quadrant: r.quadrant,
          restaurant_id: r.restaurant_id,
        };
        if (grouped[r.quadrant]) grouped[r.quadrant].push(point);
      }
      setData(grouped);
    });
  }, [kam]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Health vs Revenue
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="x"
              domain={[0, 100]}
              name="Health Score"
              label={{ value: "Health Score", position: "bottom", offset: -5 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Revenue"
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              label={{ value: "Revenue/week", angle: -90, position: "insideLeft" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              x={60}
              stroke="#94a3b8"
              strokeDasharray="5 5"
              label={{ value: "Health = 60", position: "top" }}
            />
            <ReferenceLine
              y={73383}
              stroke="#94a3b8"
              strokeDasharray="5 5"
              label={{ value: "Pareto", position: "right" }}
            />
            {Object.entries(data).map(([quadrant, points]) => (
              <Scatter
                key={quadrant}
                name={quadrant}
                data={points}
                fill={QUADRANT_COLORS[quadrant]}
                opacity={0.7}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
