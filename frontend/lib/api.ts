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

export type WeatherResponse = {
  location: string;
  latitude: number;
  longitude: number;
  source: "open_meteo" | string;
  status: string;
  message: string;
  temp_actuelle: number;
  temp_min_7j: number;
  temp_moyenne_7j: number;
  pluie_7j: boolean;
  risque_gel_7j: boolean;
  precipitation_7j: number;
  precipitation_probability_max: number;
};

export type IotLiveResponse = {
  soil_humidity: number | null;
  water_usage: number | null;
  irrigation: PredictionRequest["irrigation"] | null;
  irrigation_active: boolean | null;
  mqtt_connected: boolean;
  mqtt_status: "connected" | "reconnecting" | "disabled" | "demo";
  last_update: string | null;
  farm_id: string | null;
  soil_sensor_id: string | null;
  irrigation_sensor_id: string | null;
  water_sensor_id: string | null;
  demo: boolean;
};

export type GardenProfile = {
  location: string;
  type_sol: PredictionRequest["type_sol"];
  irrigation: PredictionRequest["irrigation"];
};

export type HealthResponse = {
  api: "ok";
  mqtt: string;
  model: string;
  database: string;
  websocket: "ok";
  demo_mode: boolean;
};

export type ModelInfoResponse = {
  name: string;
  version: string;
  type: string;
  status: string;
  classes: Recommendation[];
  metrics: Record<string, unknown>;
  model_path: string | null;
  dataset_name: string | null;
  trained_at: string | null;
};

function getApiUrl() {
  if (typeof window === "undefined") {
    return process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export function getIotWebSocketUrl() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const url = new URL(apiUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/iot";
  url.search = "";
  return url.toString();
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

export async function getWeather(location?: string): Promise<WeatherResponse> {
  const url = new URL(`${getApiUrl()}/weather`);
  if (location?.trim()) {
    url.searchParams.set("location", location.trim());
  }

  const response = await fetch(url.toString(), {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("La meteo est indisponible");
  }
  return response.json();
}

export async function getIotLive(): Promise<IotLiveResponse> {
  const response = await fetch(`${getApiUrl()}/iot/live`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("Impossible de charger les donnees IoT");
  }
  return response.json();
}

export async function getGardenProfile(): Promise<GardenProfile> {
  const response = await fetch(`${getApiUrl()}/garden/profile`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("Impossible de charger les reglages du potager");
  }
  return response.json();
}

export async function updateGardenProfile(profile: GardenProfile): Promise<GardenProfile> {
  const response = await fetch(`${getApiUrl()}/garden/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(profile)
  });
  if (!response.ok) {
    throw new Error("Impossible d'enregistrer les reglages du potager");
  }
  return response.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getApiUrl()}/health`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("API indisponible");
  }
  return response.json();
}

export async function getModelInfo(): Promise<ModelInfoResponse> {
  const response = await fetch(`${getApiUrl()}/model/info`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("Modele indisponible");
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
