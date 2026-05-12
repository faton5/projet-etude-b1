"use client";

import { useEffect, useMemo, useState } from "react";
import { GardenShell } from "@/components/GardenShell";
import {
  getGardenProfile,
  getIotLive,
  getWeather,
  type GardenProfile,
  type IotLiveResponse,
  type WeatherResponse
} from "@/lib/api";

type LoadState = "loading" | "ready" | "error";

export default function DashboardPage() {
  const [location, setLocation] = useState("Rennes");
  const [profile, setProfile] = useState<GardenProfile>({
    location: "Rennes",
    type_sol: "limoneux",
    irrigation: "manuel"
  });
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [iot, setIot] = useState<IotLiveResponse | null>(null);
  const [status, setStatus] = useState<LoadState>("loading");
  const [error, setError] = useState("");

  async function loadDashboard(currentProfile = profile) {
    setStatus("loading");
    setError("");

    try {
      const [forecast, live] = await Promise.all([
        getWeather(currentProfile.location),
        getIotLive()
      ]);
      setWeather(forecast);
      setIot(live);
      setStatus("ready");
    } catch {
      setStatus("error");
      setError("Impossible de charger les donnees en direct.");
    }
  }

  useEffect(() => {
    let activeProfile = readLocalProfile();
    setProfile(activeProfile);
    setLocation(activeProfile.location);
    loadDashboard(activeProfile);

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
    }, 60000);

    return () => window.clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const summary = useMemo(() => buildSummary(weather, iot, status), [weather, iot, status]);
  const kpis = useMemo(() => buildKpis(weather, iot, profile, status), [weather, iot, profile, status]);
  const soilHumidity = iot?.soil_humidity ?? null;
  const lastUpdate = iot?.last_update
    ? new Date(iot.last_update).toLocaleTimeString("fr-FR")
    : weather
      ? "Meteo chargee"
      : "En attente";

  return (
    <GardenShell active="home">
      <div className="flex-1 px-container-margin py-lg max-w-7xl mx-auto w-full flex flex-col gap-xl">
        <section className="bg-primary-container text-on-primary-container rounded-3xl p-xl shadow-sm border-l-8 border-primary flex flex-col md:flex-row items-start md:items-center justify-between gap-lg relative overflow-hidden">
          <span
            className="material-symbols-outlined absolute -right-8 -top-8 text-[200px] opacity-10"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            eco
          </span>
          <div className="flex flex-col gap-sm z-10">
            <h2 className="font-display-lg text-display-lg-mobile md:text-display-lg font-bold">
              {summary.title}
            </h2>
            <p className="font-status-msg text-status-msg-mobile md:text-status-msg opacity-90">
              {weather?.location ?? location} - {lastUpdate}
            </p>
          </div>
          <button
            onClick={() => loadDashboard(profile)}
            disabled={status === "loading"}
            className="z-10 bg-surface-bright text-primary px-lg py-sm rounded-full font-label-lg text-label-lg min-h-[56px] shadow-sm hover:bg-surface-variant transition-colors whitespace-nowrap disabled:opacity-70"
          >
            {status === "loading" ? "Actualisation" : "Actualiser"}
          </button>
        </section>

        <section className="bg-surface-container-low rounded-2xl p-lg flex flex-col md:flex-row items-center gap-md">
          <div className="bg-secondary-container text-on-secondary-container p-sm rounded-full flex items-center justify-center">
            <span
              className="material-symbols-outlined text-[32px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              lightbulb
            </span>
          </div>
          <div className="flex-1 text-center md:text-left">
            <p className="font-headline-md text-headline-md text-on-surface">
              {summary.recommendation}
            </p>
            <p className="font-body-lg text-body-lg text-on-surface-variant">
              {error || summary.detail}
            </p>
          </div>
        </section>

        <section className="grid grid-cols-2 md:grid-cols-5 gap-md">
          {kpis.map((kpi) => (
            <div
              key={kpi.label}
              className={`bg-surface-container rounded-2xl p-md flex flex-col items-center justify-center text-center gap-sm shadow-sm aspect-square${kpi.span ? " col-span-2 md:col-span-1" : ""}`}
            >
              <span
                className="material-symbols-outlined text-[48px] text-tertiary"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                {kpi.icon}
              </span>
              <p className="font-label-lg text-label-lg text-on-surface-variant">{kpi.label}</p>
              <p className="font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface">
                {kpi.value}
              </p>
            </div>
          ))}
        </section>

        <section className="bg-surface-container-lowest rounded-3xl p-xl shadow-sm border border-surface-variant">
          <div className="flex flex-col gap-sm md:flex-row md:items-end md:justify-between">
            <div>
              <h3 className="font-headline-lg text-headline-lg text-on-surface">
                Humidite du sol
              </h3>
              <p className="font-body-lg text-body-lg text-on-surface-variant mt-xs">
                {iot?.demo ? "Estimation de demonstration stable." : "Donnee issue du capteur IoT live."}
              </p>
            </div>
            <p className="font-display-lg text-display-lg-mobile md:text-display-lg text-primary">
              {soilHumidity == null ? "Aucune donnee" : `${soilHumidity} %`}
            </p>
          </div>

          <div className="mt-lg h-6 w-full rounded-full bg-surface-container overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${soilHumidity == null ? 0 : Math.min(Math.max(soilHumidity, 0), 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-sm font-label-lg text-label-lg text-on-surface-variant opacity-70">
            <span>Sec</span>
            <span>Ideal</span>
            <span>Humide</span>
          </div>
        </section>
      </div>
    </GardenShell>
  );
}

function buildKpis(
  weather: WeatherResponse | null,
  iot: IotLiveResponse | null,
  profile: GardenProfile,
  status: LoadState
) {
  const loading = status === "loading";

  return [
    {
      icon: "device_thermostat",
      label: "Temperature",
      value: loading ? "..." : weather ? formatTemperature(weather.temp_actuelle) : "Indispo",
      span: false
    },
    {
      icon: "water_drop",
      label: "Humidite sol",
      value: loading ? "..." : iot?.soil_humidity == null ? "Indispo" : `${iot.soil_humidity} %`,
      span: false
    },
    {
      icon: "rainy",
      label: "Pluie 7j",
      value: loading ? "..." : weather ? formatRain(weather) : "Indispo",
      span: false
    },
    {
      icon: "ac_unit",
      label: "Risque gel",
      value: loading ? "..." : weather ? (weather.risque_gel_7j ? "Oui" : "Non") : "Indispo",
      span: false
    },
    {
      icon: "sprinkler",
      label: "Irrigation",
      value: loading ? "..." : formatIrrigation(iot?.demo ? profile.irrigation : iot?.irrigation ?? profile.irrigation),
      span: true
    }
  ];
}

function buildSummary(
  weather: WeatherResponse | null,
  iot: IotLiveResponse | null,
  status: LoadState
) {
  if (status === "loading") {
    return {
      title: "Chargement des donnees du potager.",
      recommendation: "Actualisation en cours.",
      detail: "La meteo et les capteurs sont en train d'etre lus."
    };
  }

  if (!weather) {
    return {
      title: "Donnees meteo indisponibles.",
      recommendation: "Verifiez l'API ou la localisation.",
      detail: "Aucune valeur fictive n'est affichee sur le dashboard."
    };
  }

  if (weather.risque_gel_7j) {
    return {
      title: "Risque de gel detecte pour les tomates.",
      recommendation: "Attendre avant de planter.",
      detail: `Minimum prevu sur 7 jours : ${formatTemperature(weather.temp_min_7j)}.`
    };
  }

  if (iot?.soil_humidity != null && iot.soil_humidity < 35 && !weather.pluie_7j) {
    return {
      title: "Le sol est trop sec.",
      recommendation: "Prevoir un arrosage.",
      detail: `Humidite mesuree : ${iot.soil_humidity} %. Aucune pluie significative n'est prevue.`
    };
  }

  return {
    title: weather.source === "open_meteo"
      ? `Temperature actuelle : ${formatTemperature(weather.temp_actuelle)}.`
      : "Meteo reelle indisponible.",
    recommendation: weather.pluie_7j ? "Surveiller la pluie avant d'arroser." : "Conditions meteo correctes.",
    detail: weather.source === "open_meteo"
      ? `Moyenne 7 jours : ${formatTemperature(weather.temp_moyenne_7j)}. Pluie estimee : ${weather.precipitation_7j} mm.`
      : "Aucune temperature fictive n'est presentee comme une vraie mesure."
  };
}

function formatTemperature(value: number) {
  return `${Math.round(value)}°C`;
}

function formatRain(weather: WeatherResponse) {
  if (!weather.pluie_7j || weather.precipitation_7j <= 0) {
    return "Aucune";
  }
  return `${weather.precipitation_7j} mm`;
}

function formatIrrigation(value?: IotLiveResponse["irrigation"] | null) {
  return {
    manuel: "Manuel",
    goutte_a_goutte: "Goutte",
    automatique: "Auto",
    aucun: "Aucune"
  }[value ?? "aucun"];
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
