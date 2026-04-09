import type {
  PortfolioOverview,
  RestaurantSummary,
  RestaurantDetail,
  BudgetBalance,
  ChatMessage,
  SummarizeResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchDashboard(
  kam?: string
): Promise<PortfolioOverview> {
  const params = kam ? `?kam=${encodeURIComponent(kam)}` : "";
  return fetchJSON(`/api/dashboard${params}`);
}

export async function fetchRestaurants(
  kam?: string,
  quadrant?: string
): Promise<RestaurantSummary[]> {
  const params = new URLSearchParams();
  if (kam) params.set("kam", kam);
  if (quadrant) params.set("quadrant", quadrant);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return fetchJSON(`/api/dashboard/restaurants${qs}`);
}

export async function fetchRestaurantDetail(
  id: string
): Promise<RestaurantDetail> {
  return fetchJSON(`/api/dashboard/restaurants/${id}`);
}

export async function fetchAlerts(
  kam?: string
): Promise<RestaurantSummary[]> {
  const params = kam ? `?kam=${encodeURIComponent(kam)}` : "";
  return fetchJSON(`/api/dashboard/alerts${params}`);
}

export async function fetchBudget(kam: string): Promise<BudgetBalance> {
  return fetchJSON(`/api/budget?kam=${encodeURIComponent(kam)}`);
}

export async function* streamChat(
  kam: string,
  messages: ChatMessage[]
): AsyncGenerator<string> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kam, messages }),
  });

  if (!res.ok) throw new Error(`Chat API error: ${res.status}`);
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (!data) continue;
      let parsed: { content?: string; error?: string };
      try {
        parsed = JSON.parse(data);
      } catch {
        continue; // skip malformed JSON
      }
      if (parsed.error) throw new Error(parsed.error);
      if (parsed.content) yield parsed.content;
    }
  }
}

export async function summarizeChat(
  kam: string,
  messages: ChatMessage[]
): Promise<SummarizeResponse> {
  const res = await fetch(`${API_URL}/api/chat/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kam, messages }),
  });
  if (!res.ok) throw new Error(`Summarize API error: ${res.status}`);
  return res.json();
}
