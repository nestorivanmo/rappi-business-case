export interface PortfolioOverview {
  total_restaurants: number;
  quadrant_distribution: {
    GROW: number;
    RESCUE: number;
    NURTURE: number;
    TRIAGE: number;
  };
  total_revenue: number;
  revenue_at_risk: number;
  velocity_alert_count: number;
}

export interface RestaurantSummary {
  restaurant_id: string;
  nombre: string;
  ciudad: string;
  vertical: string;
  health_score: number;
  quadrant: string;
  weekly_revenue: number;
  escalation_level: string;
  time_horizon: string;
  dominant_risk_signals: string[];
  velocity_flag: boolean;
  rating_actual: number;
  delta_rating: number;
  valor_ticket_prom_mxn: number;
  tasa_cancelacion_pct: number;
  tiempo_entrega_avg_min: number;
}

export interface RestaurantDetail extends RestaurantSummary {
  rating_actual: number;
  rating_prom_30d: number;
  delta_rating: number;
  tasa_cancelacion_pct: number;
  tiempo_entrega_avg_min: number;
  quejas_7d: number;
  var_ordenes_pct: number;
  nps_score: number;
  ordenes_7d: number;
  valor_ticket_prom_mxn: number;
  signals_normalized: Record<string, number>;
  kam_asignado: string;
  activo_desde: string;
  semaforo_riesgo: string;
}

export interface BudgetBalance {
  kam_name: string;
  remaining: number;
  total_allocated: number;
  total_spent: number;
  spend_by_category: Record<string, number>;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export type Quadrant = "GROW" | "RESCUE" | "NURTURE" | "TRIAGE";
