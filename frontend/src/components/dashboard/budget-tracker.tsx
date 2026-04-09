"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/constants";
import type { BudgetBalance } from "@/lib/types";

export function BudgetTracker({ budget }: { budget?: BudgetBalance }) {
  if (!budget) return null;

  const pct = (budget.total_spent / budget.total_allocated) * 100;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Weekly Budget</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">
              {formatCurrency(budget.total_spent)} spent
            </span>
            <span className="font-medium">
              {formatCurrency(budget.remaining)} left
            </span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-orange-500 rounded-full transition-all"
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            of {formatCurrency(budget.total_allocated)}
          </p>
        </div>

        {Object.keys(budget.spend_by_category).length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Spend by category
            </p>
            <div className="space-y-1">
              {Object.entries(budget.spend_by_category).map(([cat, amount]) => (
                <div key={cat} className="flex justify-between text-xs">
                  <span className="capitalize">{cat.replace("_", " ")}</span>
                  <span>{formatCurrency(amount)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
