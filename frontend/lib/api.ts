export type Recommendation = "viable" | "attendre" | "non_viable";

export type PredictionRequest = {
  location: string;
  culture: "tomate";
  saison: "printemps" | "ete" | "automne" | "hiver";
  type_sol: "argileux" | "limoneux" | "sableux" | "calcaire" | "humifere";
  irrigation: "manuel" | "goutte_a_goutte" | "automatique" | "aucun";
  humidite_sol: number;
  temp_actuelle: number;
  temp_min_7j: number;
  temp_moyenne_7j: number;
  pluie_7j: boolean;
  risque_gel_7j: boolean;
  water_usage: number;
};

export type PredictionResponse = {
  id: number;
  created_at: string;
  recommandation: Recommendation;
  score_confiance: number;
  explication: string;
  facteurs_importants: string[];
};

export type HistoryItem = PredictionResponse & {
  request: PredictionRequest;
};

function getApiUrl() {
  if (typeof window === "undefined") {
    return process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export async function getHistory(limit = 20): Promise<HistoryItem[]> {
  const response = await fetch(`${getApiUrl()}/history?limit=${limit}`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("Impossible de charger l'historique");
  }
  return response.json();
}

export async function createPrediction(payload: PredictionRequest): Promise<PredictionResponse> {
  const response = await fetch(`${getApiUrl()}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("La prediction a echoue");
  }
  return response.json();
}

export function formatRecommendation(value: Recommendation) {
  return {
    viable: "Planter",
    attendre: "Attendre",
    non_viable: "Ne pas planter"
  }[value];
}
