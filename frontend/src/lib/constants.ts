export const KAM_LIST = [
  "Ana Torres",
  "Carlos Mendoza",
  "Diego Vargas",
  "Fernando Castro",
  "Isabella Moreno",
  "Juan Perez",
  "Maria Lopez",
  "Paula Herrera",
  "Roberto Sanchez",
  "Sofia Ramirez",
];

export const QUADRANT_COLORS: Record<string, string> = {
  GROW: "#22c55e",
  RESCUE: "#ef4444",
  NURTURE: "#3b82f6",
  TRIAGE: "#6b7280",
};

export const QUADRANT_LABELS: Record<string, string> = {
  GROW: "Grow",
  RESCUE: "Rescue",
  NURTURE: "Nurture",
  TRIAGE: "Triage",
};

export const SIGNAL_LABELS: Record<string, string> = {
  delta_rating: "Rating Velocity",
  tasa_cancelacion_pct: "Cancellation Rate",
  quejas_7d: "Weekly Complaints",
  rating_actual: "Current Rating",
  tiempo_entrega_avg_min: "Delivery Time",
  var_ordenes_pct: "Order Volume Change",
};

export function kamToSlug(name: string): string {
  return name.toLowerCase().replace(/ /g, "-");
}

export function slugToKam(slug: string): string {
  const found = KAM_LIST.find((k) => kamToSlug(k) === slug);
  return found || KAM_LIST[0];
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    maximumFractionDigits: 0,
  }).format(value);
}
