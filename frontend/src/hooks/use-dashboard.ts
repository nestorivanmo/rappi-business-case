"use client";

import useSWR from "swr";
import { fetchDashboard, fetchAlerts, fetchBudget, fetchRestaurants } from "@/lib/api";
import type { PortfolioOverview, RestaurantSummary, BudgetBalance } from "@/lib/types";

export function useDashboard(kam: string) {
  const { data: overview, error: overviewError, isLoading: overviewLoading } = useSWR<PortfolioOverview>(
    `dashboard-${kam}`,
    () => fetchDashboard(kam),
    { refreshInterval: 30000 }
  );

  const { data: alerts, error: alertsError, isLoading: alertsLoading } = useSWR<RestaurantSummary[]>(
    `alerts-${kam}`,
    () => fetchAlerts(kam),
    { refreshInterval: 30000 }
  );

  const { data: budget, error: budgetError, isLoading: budgetLoading } = useSWR<BudgetBalance>(
    `budget-${kam}`,
    () => fetchBudget(kam),
    { refreshInterval: 30000 }
  );

  const { data: restaurants, error: restaurantsError, isLoading: restaurantsLoading } = useSWR<RestaurantSummary[]>(
    `restaurants-${kam}`,
    () => fetchRestaurants(kam),
    { refreshInterval: 30000 }
  );

  return {
    overview,
    alerts,
    budget,
    restaurants,
    isLoading: overviewLoading || alertsLoading || budgetLoading || restaurantsLoading,
    error: overviewError || alertsError || budgetError || restaurantsError,
  };
}
