"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { GardenShell } from "@/components/GardenShell";
import {
  getGardenProfile,
  getIotLive,
  getWeather,
  getWateringAdvice,
  type GardenProfile,
  type IotLiveResponse,
  type WeatherResponse,
  type WateringAdviceResponse
} from "@/lib/api";

type LoadState = "loading" | "ready" | "error";
type SummaryTone = "ok" | "water" | "watch" | "urgent";
const AUTO_REFRESH_MS = 10 * 60 * 1000;
const WEATHER_RETRY_MS = 2 * 60 * 1000;

export default function DashboardPage() {
  const retryTimeout = useRef<number | null>(null);
  const [location, setLocation] = useState("Rennes");
  const [profile, setProfile] = useState<GardenProfile>({
    location: "Rennes",
    type_sol: "limoneux",
    irrigation: "manuel"
  });
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [iot, setIot] = useState<IotLiveResponse | null>(null);
  const [advice, setAdvice] = useState<WateringAdviceResponse | null>(null);
  const [status, setStatus] = useState<LoadState>("loading");
  const [error, setError] = useState("");

  function clearWeatherRetry() {
    if (retryTimeout.current) {
      window.clearTimeout(retryTimeout.current);
      retryTimeout.current = null;
    }
  }

  function scheduleWeatherRetry(currentProfile: GardenProfile) {
    clearWeatherRetry();
    retryTimeout.current = window.setTimeout(() => {
      loadDashboard(currentProfile);
    }, WEATHER_RETRY_MS);
  }

  async function loadDashboard(currentProfile = profile, showLoading = false) {
    if (showLoading) {
      setStatus("loading");
    }
    setError("");

    const [forecastResult, liveResult] = await Promise.allSettled([
      getWeather(currentProfile.location),
      getIotLive()
    ]);

    let forecast: WeatherResponse | null = null;
    let live: IotLiveResponse | null = null;

    if (forecastResult.status === "fulfilled") {
      forecast = forecastResult.value;
      setWeather(forecast);
      if (isRealWeather(forecast)) {
        clearWeatherRetry();
      } else {
        setError("On attend la météo. Les informations vont revenir seules.");
        scheduleWeatherRetry(currentProfile);
      }
    } else {
      setWeather(null);
      setError("On attend la météo. Les informations vont revenir seules.");
      scheduleWeatherRetry(currentProfile);
    }

    if (liveResult.status === "fulfilled") {
      live = liveResult.value;
      setIot(live);
    } else {
      setIot(null);
      setError((current) => current || "Les mesures du jardin ne sont pas disponibles pour l'instant.");
    }

    // Récupérer le conseil d'arrosage pour le jardin.
    if (forecast || live) {
      try {
        const wateringAdvice = await getWateringAdvice({
          location: currentProfile.location,
          type_sol: currentProfile.type_sol,
          irrigation: currentProfile.irrigation,
          humidite_sol: live?.soil_humidity ?? undefined,
          temp_actuelle: forecast?.temp_actuelle,
          temp_min_7j: forecast?.temp_min_7j,
          temp_moyenne_7j: forecast?.temp_moyenne_7j,
          pluie_7j: forecast?.pluie_7j,
          precipitation_7j: forecast?.precipitation_7j
        });
        setAdvice(wateringAdvice);
      } catch {
        setAdvice(null);
      }
    }

    if (forecastResult.status === "fulfilled" || liveResult.status === "fulfilled") {
      setStatus("ready");
    } else {
      setStatus("error");
    }
  }

  useEffect(() => {
    let activeProfile = readLocalProfile();
    setProfile(activeProfile);
    setLocation(activeProfile.location);
    loadDashboard(activeProfile, true);

    getGardenProfile()
      .then((apiProfile) => {
        activeProfile = apiProfile;
        setProfile(apiProfile);
        setLocation(apiProfile.location);
        writeLocalProfile(apiProfile);
        loadDashboard(apiProfile);
      })
      .catch(() => undefined);

    const interval = window.setInterval(() => {
      loadDashboard(activeProfile);
    }, AUTO_REFRESH_MS);

    return () => {
      window.clearInterval(interval);
      clearWeatherRetry();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const summary = useMemo(() => buildSummary(weather, iot, advice, status), [weather, iot, advice, status]);
  const kpis = useMemo(() => buildKpis(weather, iot, status), [weather, iot, status]);
  const tone = toneStyles[summary.tone];
  const detailText = error && !advice ? error : summary.detail;
  const soilHumidity = iot?.soil_humidity ?? null;
  const updateLabel = status === "loading" ? "Lecture en cours" : weather || iot ? "Mis à jour récemment" : "En attente";
  const soilState = getSoilState(soilHumidity);

  return (
    <GardenShell active="home">
      <div className="dashboard-content flex-1 py-lg min-w-0 overflow-x-hidden flex flex-col gap-lg md:gap-xl">
        <section className={`${tone.hero} rounded-3xl p-md md:p-xl shadow-sm border-l-8 ${tone.border} flex flex-col gap-md relative overflow-hidden`}>
          <span
            className="material-symbols-outlined absolute -right-8 -top-8 text-[180px] opacity-10"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            {summary.icon}
          </span>
          <div className="flex flex-col gap-sm z-10 max-w-[300px] md:max-w-4xl min-w-0">
            <p className="font-label-lg text-label-lg opacity-90">{summary.badge}</p>
            <h2 className="font-display-lg text-[38px] leading-[44px] md:text-[56px] md:leading-[62px] font-bold break-words">
              {summary.title}
            </h2>
            <p className="font-status-msg text-status-msg-mobile md:text-status-msg opacity-95 break-words">
              {summary.reason}
            </p>
          </div>
          <p className="z-10 font-body-md text-body-md opacity-85">
            {weather?.location ?? location} - {updateLabel}
          </p>
        </section>

        <section className="bg-surface-container-low rounded-2xl p-md md:p-lg flex flex-col md:flex-row items-center gap-md">
          <div className={`${tone.badgeBg} ${tone.badgeText} p-sm rounded-full flex items-center justify-center`}>
            <span
              className="material-symbols-outlined text-[32px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              schedule
            </span>
          </div>
          <div className="flex-1 min-w-0 w-full max-w-[300px] md:max-w-none mx-auto md:mx-0 text-center md:text-left">
            <p className="font-headline-md text-headline-md text-on-surface break-words">
              {summary.nextStep}
            </p>
            <p className="font-body-lg text-body-lg text-on-surface-variant break-words">
              {detailText}
            </p>
          </div>
        </section>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-sm md:gap-md">
          {kpis.map((kpi) => (
            <div
              key={kpi.label}
              className="bg-surface-container rounded-2xl p-md flex flex-col items-center justify-center text-center gap-xs shadow-sm min-h-[136px]"
            >
              <span
                className="material-symbols-outlined text-[36px] text-tertiary"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                {kpi.icon}
              </span>
              <p className="font-label-lg text-label-lg text-on-surface-variant">{kpi.label}</p>
              <p className="font-headline-lg text-headline-lg text-on-surface">
                {kpi.value}
              </p>
            </div>
          ))}
        </section>

        <section className="bg-surface-container-lowest rounded-3xl p-lg shadow-sm border border-surface-variant">
          <div className="flex flex-col gap-sm md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="font-headline-md text-headline-md text-on-surface">
                État de la terre
              </h3>
              <p className="font-body-lg text-body-lg text-on-surface-variant mt-xs">
                {iot?.demo ? "Valeur approximative." : "Mesure du jardin."}
              </p>
            </div>
            <p className={`font-headline-lg text-headline-lg ${soilState.textClass}`}>
              {soilState.label}
            </p>
          </div>

          <div className="mt-md h-3 w-full rounded-full bg-surface-container overflow-hidden">
            <div
              className={`h-full rounded-full ${soilState.barClass} transition-all duration-500`}
              style={{ width: `${soilHumidity == null ? 0 : Math.min(Math.max(soilHumidity, 0), 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-sm font-label-lg text-label-lg text-on-surface-variant opacity-70">
            <span>Sol sec</span>
            <span>Sol correct</span>
            <span>Humide</span>
          </div>
        </section>

        <section className="bg-surface-container-low rounded-2xl p-md md:p-lg">
          <h3 className="font-headline-md text-headline-md text-on-surface">Dernier point</h3>
          <p className="font-body-lg text-body-lg text-on-surface-variant mt-xs">
            {summary.history}
          </p>
        </section>
      </div>
    </GardenShell>
  );
}

const toneStyles: Record<SummaryTone, {
  hero: string;
  border: string;
  badgeBg: string;
  badgeText: string;
}> = {
  ok: {
    hero: "bg-primary-container text-on-primary-container",
    border: "border-primary",
    badgeBg: "bg-primary-fixed",
    badgeText: "text-on-primary-fixed"
  },
  water: {
    hero: "bg-tertiary-container text-on-tertiary-container",
    border: "border-tertiary",
    badgeBg: "bg-tertiary-fixed",
    badgeText: "text-on-tertiary-fixed"
  },
  watch: {
    hero: "bg-secondary-container text-on-secondary-container",
    border: "border-secondary",
    badgeBg: "bg-secondary-fixed",
    badgeText: "text-on-secondary-fixed"
  },
  urgent: {
    hero: "bg-error-container text-on-error-container",
    border: "border-error",
    badgeBg: "bg-error",
    badgeText: "text-on-error"
  }
};

function buildKpis(
  weather: WeatherResponse | null,
  iot: IotLiveResponse | null,
  status: LoadState
) {
  const loading = status === "loading";
  const realWeather = isRealWeather(weather);

  return [
    {
      icon: "device_thermostat",
      label: "Température",
      value: loading ? "..." : realWeather ? formatTemperature(weather.temp_actuelle) : "Non disponible"
    },
    {
      icon: "water_drop",
      label: "Terre humide",
      value: loading ? "..." : iot?.soil_humidity == null ? "Non disponible" : `${Math.round(iot.soil_humidity)} %`
    },
    {
      icon: "rainy",
      label: "Pluie cette semaine",
      value: loading ? "..." : realWeather ? formatRain(weather) : "Non disponible"
    },
    {
      icon: "ac_unit",
      label: "Risque de gel",
      value: loading ? "..." : realWeather ? (weather.risque_gel_7j ? "Oui" : "Non") : "Non disponible"
    }
  ];
}

function buildSummary(
  weather: WeatherResponse | null,
  iot: IotLiveResponse | null,
  advice: WateringAdviceResponse | null,
  status: LoadState
) {
  if (status === "loading") {
    return {
      tone: "watch" as SummaryTone,
      icon: "hourglass_top",
      badge: "Lecture du jardin",
      title: "On regarde le potager",
      reason: "Les informations arrivent dans quelques instants.",
      nextStep: "Attendre quelques secondes",
      detail: "La page se met à jour toute seule.",
      history: "Dernier point en cours de préparation."
    };
  }

  const hasRealData = weather?.source === "open_meteo";

  if (weather?.risque_gel_7j) {
    return {
      tone: "urgent" as SummaryTone,
      icon: "ac_unit",
      badge: "Urgent",
      title: "Attention au gel",
      reason: "Le froid arrive et les plants peuvent souffrir.",
      nextStep: "Protéger les plants ou attendre avant de planter",
      detail: `Température la plus basse prévue : ${formatTemperature(weather.temp_min_7j)}.`,
      history: "Dernier point : risque de gel à surveiller en priorité."
    };
  }

  if (advice) {
    return buildActionSummary(weather, iot, advice, hasRealData);
  }

  if (!weather) {
    return {
      tone: "watch" as SummaryTone,
      icon: "cloud_off",
      badge: "À surveiller",
      title: "On attend la météo",
      reason: "Les informations météo ne sont pas encore revenues.",
      nextStep: "Vérifier le potager normalement",
      detail: "Aucune action urgente n'est indiquée pour le moment.",
      history: "Dernier point incomplet : la météo n'est pas disponible."
    };
  }

  const soilHumidity = iot?.soil_humidity;

  return {
    tone: weather.pluie_7j ? "ok" as SummaryTone : "watch" as SummaryTone,
    icon: weather.pluie_7j ? "rainy" : "visibility",
    badge: weather.pluie_7j ? "Tout va bien" : "À surveiller",
    title: weather.pluie_7j ? "Attendre avant d'arroser" : "Surveiller aujourd'hui",
    reason: soilHumidity != null
      ? `La terre est à ${Math.round(soilHumidity)} %${weather.pluie_7j ? " et la pluie est prévue." : "."}`
      : "Il manque l'information sur la terre.",
    nextStep: weather.pluie_7j ? "Laisser la pluie faire" : "Regarder la terre plus tard",
    detail: hasRealData
      ? `Température actuelle : ${formatTemperature(weather.temp_actuelle)}.`
      : "Les informations sont partielles pour le moment.",
    history: "Dernier point : pas de conseil détaillé disponible."
  };
}

function buildActionSummary(
  weather: WeatherResponse | null,
  iot: IotLiveResponse | null,
  advice: WateringAdviceResponse,
  hasRealData: boolean
) {
  const soilText = iot?.soil_humidity != null ? `La terre est à ${Math.round(iot.soil_humidity)} %.` : "";
  const rainText = weather
    ? weather.pluie_7j ? "De la pluie est prévue cette semaine." : "Aucune pluie n'est prévue."
    : "La météo est en attente.";
  const detail = `${humanizeAction(advice.recommandation_action)} ${humanizeCheck(advice.prochaine_verification)}`;
  const history = `${humanizeAdvice(advice.conseil)} ${hasRealData ? rainText : "Les informations sont partielles."}`;

  if (advice.priorite === "urgent") {
    return {
      tone: "urgent" as SummaryTone,
      icon: "water_drop",
      badge: "Urgent",
      title: "Arroser maintenant",
      reason: soilText || "La terre manque d'eau.",
      nextStep: "Arroser dès que possible",
      detail,
      history
    };
  }

  if (advice.priorite === "eleve") {
    return {
      tone: "water" as SummaryTone,
      icon: "water_drop",
      badge: "À faire",
      title: "Arroser aujourd'hui",
      reason: `${soilText} ${rainText}`.trim(),
      nextStep: "Prévoir un arrosage",
      detail,
      history
    };
  }

  if (advice.priorite === "moyen") {
    return {
      tone: "watch" as SummaryTone,
      icon: "visibility",
      badge: "À surveiller",
      title: advice.conseil.toLowerCase().includes("pluie") ? "Attendre la pluie" : "Surveiller aujourd'hui",
      reason: `${soilText} ${rainText}`.trim(),
      nextStep: "Regarder l'évolution du jardin",
      detail,
      history
    };
  }

  if (weather?.pluie_7j && (advice.conseil.toLowerCase().includes("reporter") || advice.conseil.toLowerCase().includes("pluie"))) {
    return {
      tone: "ok" as SummaryTone,
      icon: "rainy",
      badge: "Tout va bien",
      title: "Attendre avant d'arroser",
      reason: `${soilText} ${rainText}`.trim(),
      nextStep: "Ne pas arroser pour le moment",
      detail,
      history
    };
  }

  return {
    tone: "ok" as SummaryTone,
    icon: "check_circle",
    badge: "Tout va bien",
    title: "Rien à faire aujourd'hui",
    reason: soilText || "Le potager est dans un état correct.",
    nextStep: "Continuer la surveillance habituelle",
    detail,
    history
  };
}

function formatTemperature(value: number) {
  return `${Math.round(value)}°C`;
}

function isRealWeather(weather: WeatherResponse | null): weather is WeatherResponse {
  return weather?.source === "open_meteo";
}

function formatRain(weather: WeatherResponse) {
  if (!weather.pluie_7j || weather.precipitation_7j <= 0) {
    return "Aucune";
  }
  return `${weather.precipitation_7j} mm`;
}

function getSoilState(value: number | null) {
  if (value == null) {
    return {
      label: "Pas d'information pour l'instant",
      textClass: "text-on-surface-variant",
      barClass: "bg-outline"
    };
  }

  if (value < 35) {
    return {
      label: "Sol sec",
      textClass: "text-tertiary",
      barClass: "bg-tertiary"
    };
  }

  if (value > 75) {
    return {
      label: "Sol humide",
      textClass: "text-primary",
      barClass: "bg-primary"
    };
  }

  return {
    label: "Sol correct",
    textClass: "text-primary",
    barClass: "bg-primary"
  };
}

function humanizeAdvice(value: string) {
  return value
    .replace("Reporter l'arrosage - Pluie prevue", "Arrosage reporté : pluie prévue.")
    .replace("Aucun arrosage necessaire - Sol sature", "Pas d'arrosage : la terre est très humide.")
    .replace("Aucun arrosage necessaire - Sol bien hydrate", "Pas d'arrosage : la terre est bien humide.")
    .replace("Sol en bon etat - Surveillance reguliere", "La terre est en bon état.");
}

function humanizeAction(value: string) {
  return value
    .replace("Arroser immediatement", "Arroser dès que possible")
    .replace("Pas d'arrosage necessaire", "Pas besoin d'arroser")
    .replace("Reverifier", "Revérifier")
    .replace("reevaluer", "regarder de nouveau")
    .replace("Completer", "Compléter")
    .replace("m2", "m²");
}

function humanizeCheck(value: string) {
  return value
    .replace("Verifier", "Vérifier")
    .replace("Reverifier", "Revérifier")
    .replace("apres", "après");
}

function readLocalProfile(): GardenProfile {
  return {
    location: window.localStorage.getItem("potager.location") || "Rennes",
    type_sol: normalizeSoilType(window.localStorage.getItem("potager.soilType")) || "limoneux",
    irrigation: normalizeIrrigation(window.localStorage.getItem("potager.irrigation")) || "manuel"
  };
}

function writeLocalProfile(profile: GardenProfile) {
  window.localStorage.setItem("potager.location", profile.location);
  window.localStorage.setItem("potager.soilType", profile.type_sol);
  window.localStorage.setItem("potager.irrigation", profile.irrigation);
}

function normalizeSoilType(value: string | null): GardenProfile["type_sol"] | null {
  if (value === "clay") {
    return "argileux";
  }
  if (value === "sand") {
    return "sableux";
  }
  if (value === "silt") {
    return "limoneux";
  }
  if (value === "argileux" || value === "limoneux" || value === "sableux" || value === "calcaire" || value === "humifere") {
    return value;
  }
  return null;
}

function normalizeIrrigation(value: string | null): GardenProfile["irrigation"] | null {
  if (value === "manuel" || value === "goutte_a_goutte" || value === "automatique" || value === "aucun") {
    return value;
  }
  return null;
}
