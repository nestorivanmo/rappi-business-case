"use client";

import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { fetchDashboard, fetchAlerts, fetchBudget, fetchRestaurants } from "@/lib/api";
import type { PortfolioOverview, RestaurantSummary, BudgetBalance } from "@/lib/types";

export function useDashboard(kam: string) {
  const { mutate } = useSWRConfig();

  // Detect KAM change during render (React 19's recommended pattern for
  // resetting state in response to prop changes). Setting state during render
  // triggers a re-render before committing, which avoids the cascading-render
  // pitfall of setting state inside useEffect.
  const [prevKam, setPrevKam] = useState(kam);
  const [isSwitching, setIsSwitching] = useState(false);
  if (kam !== prevKam) {
    setPrevKam(kam);
    setIsSwitching(true);
  }

  // Once a switch is pending, force fresh fetches (ignoring SWR cache) so
  // skeletons always render during the transition — even when re-visiting a
  // previously loaded KAM.
  useEffect(() => {
    if (!isSwitching) return;
    let cancelled = false;
    Promise.all([
      mutate(`dashboard-${kam}`, undefined, { revalidate: true }),
      mutate(`alerts-${kam}`, undefined, { revalidate: true }),
      mutate(`budget-${kam}`, undefined, { revalidate: true }),
      mutate(`restaurants-${kam}`, undefined, { revalidate: true }),
    ])
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setIsSwitching(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isSwitching, kam, mutate]);

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
    isLoading:
      isSwitching ||
      overviewLoading ||
      alertsLoading ||
      budgetLoading ||
      restaurantsLoading,
    error: overviewError || alertsError || budgetError || restaurantsError,
  };
}
