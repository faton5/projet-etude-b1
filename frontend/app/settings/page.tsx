"use client";

import { useEffect, useState } from "react";
import { GardenShell } from "@/components/GardenShell";
import {
  getGardenProfile,
  updateGardenProfile,
  type GardenProfile,
  type PredictionRequest
} from "@/lib/api";

type SoilType = PredictionRequest["type_sol"];
type IrrigationMode = PredictionRequest["irrigation"];

const soilOptions: { id: SoilType; icon: string; label: string; desc: string }[] = [
  { id: "limoneux", icon: "psychiatry", label: "Je ne sais pas", desc: "Choix par defaut : terre de jardin classique." },
  { id: "argileux", icon: "texture", label: "Terre lourde", desc: "Colle aux chaussures, reste humide longtemps." },
  { id: "sableux", icon: "grain", label: "Terre legere", desc: "S'effrite facilement et seche vite." },
  { id: "humifere", icon: "compost", label: "Terre avec compost", desc: "Sombre, souple, riche en matiere organique." }
];

const irrigationOptions: { id: IrrigationMode; label: string }[] = [
  { id: "manuel", label: "Arrosage a la main" },
  { id: "goutte_a_goutte", label: "Goutte-a-goutte" },
  { id: "automatique", label: "Programmateur" },
  { id: "aucun", label: "Pas d'arrosage" }
];

const notifOptions = [
  { key: "watering" as const, label: "Rappels d'arrosage", desc: "Etre prevenu quand les plants manquent d'eau." },
  { key: "weather" as const, label: "Alertes meteo", desc: "Suivi du gel, de la pluie et des fortes chaleurs." },
  { key: "harvest" as const, label: "Recolte prete", desc: "Alertes lorsque les tomates arrivent a maturite." }
];

export default function SettingsPage() {
  const [location, setLocation] = useState("Rennes");
  const [soilType, setSoilType] = useState<SoilType>("limoneux");
  const [irrigation, setIrrigation] = useState<IrrigationMode>("manuel");
  const [notifications, setNotifications] = useState({ watering: true, weather: false, harvest: true });
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState("");

  useEffect(() => {
    const localProfile = readLocalProfile();
    if (localProfile) {
      setLocation(localProfile.location);
      setSoilType(localProfile.type_sol);
      setIrrigation(localProfile.irrigation);
    }

    getGardenProfile()
      .then((profile) => {
        setLocation(profile.location);
        setSoilType(profile.type_sol);
        setIrrigation(profile.irrigation);
        writeLocalProfile(profile);
      })
      .catch(() => undefined);
  }, []);

  async function savePreferences() {
    const profile: GardenProfile = {
      location: location.trim() || "Rennes",
      type_sol: soilType,
      irrigation
    };
    setSaveError("");

    try {
      const savedProfile = await updateGardenProfile(profile);
      writeLocalProfile(savedProfile);
      setLocation(savedProfile.location);
      setSoilType(savedProfile.type_sol);
      setIrrigation(savedProfile.irrigation);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    } catch {
      writeLocalProfile(profile);
      setSaved(true);
      setSaveError("Reglages gardes sur ce navigateur. L'API ne les a pas encore recus.");
      window.setTimeout(() => setSaved(false), 2500);
    }
  }

  return (
    <GardenShell active="settings">
      <div className="p-container-margin md:p-xl max-w-5xl mx-auto w-full">
        <div className="mb-lg">
          <h1 className="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface mb-xs">
            Reglages
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Configurez le potager, la localisation et les alertes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg">
          <div className="md:col-span-8 flex flex-col gap-lg">

            {/* Localisation */}
            <section className="bg-surface-container-lowest rounded-xl p-md shadow-sm border border-surface-variant">
              <div className="flex items-center gap-sm mb-md">
                <div className="w-10 h-10 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center">
                  <span className="material-symbols-outlined">location_on</span>
                </div>
                <h2 className="font-headline-md text-headline-md text-on-surface">Localisation</h2>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant mb-4">
                Saisissez librement la ville ou le lieu du potager pour la meteo et les predictions.
              </p>
              <label className="grid gap-2">
                <span className="font-label-lg text-label-lg text-on-surface-variant">Ville ou adresse</span>
                <input
                  className="w-full bg-surface border-b-2 border-primary text-on-surface font-body-md text-body-md py-3 px-4 rounded-t-md shadow-sm focus:outline-none"
                  list="location-suggestions"
                  value={location}
                  onChange={(event) => setLocation(event.target.value)}
                  placeholder="Ex : Rennes, Nantes, EHPAD Les Jardins..."
                />
              </label>
              <datalist id="location-suggestions">
                <option value="Rennes" />
                <option value="Paris" />
                <option value="Lyon" />
                <option value="Marseille" />
                <option value="Bordeaux" />
                <option value="Nantes" />
              </datalist>
            </section>

            {/* Type de sol */}
            <section className="bg-surface-container-lowest rounded-xl p-md shadow-sm border border-surface-variant">
              <div className="flex items-center gap-sm mb-md">
                <div className="w-10 h-10 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center">
                  <span className="material-symbols-outlined">landscape</span>
                </div>
                <h2 className="font-headline-md text-headline-md text-on-surface">Type de sol</h2>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant mb-4">
                Si vous ne savez pas, gardez le choix par defaut. Le systeme partira sur une terre de jardin classique.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
                {soilOptions.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setSoilType(s.id)}
                    className={`flex flex-col items-center justify-center p-md rounded-lg border-2 transition-colors ${
                      soilType === s.id
                        ? "border-primary bg-primary-fixed-dim/20"
                        : "border-transparent bg-surface-container hover:bg-surface-variant"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined mb-2 text-4xl ${soilType === s.id ? "text-primary" : "text-on-surface-variant"}`}
                    >
                      {s.icon}
                    </span>
                    <span className="font-label-lg text-label-lg text-on-surface">{s.label}</span>
                    <span className="mt-1 text-sm text-on-surface-variant">{s.desc}</span>
                  </button>
                ))}
              </div>
            </section>

            {/* Mode irrigation */}
            <section className="bg-surface-container-lowest rounded-xl p-md shadow-sm border border-surface-variant">
              <div className="flex items-center gap-sm mb-md">
                <div className="w-10 h-10 rounded-full bg-tertiary-container text-on-tertiary-container flex items-center justify-center">
                  <span className="material-symbols-outlined">water_drop</span>
                </div>
                <h2 className="font-headline-md text-headline-md text-on-surface">Mode irrigation</h2>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant mb-4">
                Choisissez comment l&apos;arrosage est gere.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-sm bg-surface-container p-1 rounded-lg">
                {irrigationOptions.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => setIrrigation(option.id)}
                    className={`py-3 px-3 text-center rounded-md font-label-lg text-label-lg transition-all ${
                      irrigation === option.id
                        ? "bg-surface shadow-sm text-on-surface"
                        : "text-on-surface-variant hover:text-on-surface"
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </section>

            {/* Notifications */}
            <section className="bg-surface-container-lowest rounded-xl p-md shadow-sm border border-surface-variant">
              <div className="flex items-center gap-sm mb-md">
                <div className="w-10 h-10 rounded-full bg-surface-variant text-on-surface-variant flex items-center justify-center">
                  <span className="material-symbols-outlined">notifications</span>
                </div>
                <h2 className="font-headline-md text-headline-md text-on-surface">Notifications</h2>
              </div>
              <div className="flex flex-col gap-sm">
                {notifOptions.map((n, i) => (
                  <div
                    key={n.key}
                    className={`flex items-center justify-between py-3 ${i < notifOptions.length - 1 ? "border-b border-surface-variant" : ""}`}
                  >
                    <div>
                      <div className="font-label-lg text-label-lg text-on-surface">{n.label}</div>
                      <div className="text-sm text-on-surface-variant">{n.desc}</div>
                    </div>
                    <button
                      onClick={() => setNotifications((prev) => ({ ...prev, [n.key]: !prev[n.key] }))}
                      className={`w-12 h-6 rounded-full relative transition-colors focus:outline-none ${
                        notifications[n.key] ? "bg-primary" : "bg-surface-dim"
                      }`}
                    >
                      <div
                        className={`absolute top-1 w-4 h-4 rounded-full transition-all ${
                          notifications[n.key] ? "right-1 bg-on-primary" : "left-1 bg-outline"
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Info Sidebar */}
          <div className="md:col-span-4 hidden md:block">
            <div className="bg-surface-container-high rounded-xl p-md shadow-sm sticky top-xl">
              <div className="flex items-start gap-sm mb-md">
                <span className="material-symbols-outlined text-primary text-3xl">eco</span>
                <div>
                  <h3 className="font-status-msg text-status-msg text-on-surface">Sante du potager</h3>
                  <p className="font-body-md text-body-md text-on-surface-variant mt-2">
                    Ces reglages sont maintenant envoyes a l&apos;API et repris dans le dashboard et la prediction.
                    Le type de sol sert seulement a ajuster la retention d&apos;eau.
                  </p>
                  {saveError && (
                    <p className="mt-3 rounded-md bg-surface p-3 text-sm text-on-surface-variant">
                      {saveError}
                    </p>
                  )}
                </div>
              </div>
              <div className="mt-lg pt-md border-t border-outline-variant">
                <button
                  onClick={savePreferences}
                  className="w-full bg-primary hover:bg-primary-container text-on-primary font-label-lg text-label-lg py-4 rounded-lg shadow-sm transition-colors flex items-center justify-center gap-sm min-h-[56px]"
                >
                  <span className="material-symbols-outlined">save</span>
                  {saved ? "Preferences enregistrees" : "Enregistrer"}
                </button>
              </div>
            </div>
          </div>
        </div>
        <button
          onClick={savePreferences}
          className="mt-lg flex w-full items-center justify-center gap-sm rounded-lg bg-primary py-4 font-label-lg text-label-lg text-on-primary shadow-sm transition-colors hover:bg-primary-container md:hidden"
        >
          <span className="material-symbols-outlined">save</span>
          {saved ? "Preferences enregistrees" : "Enregistrer"}
        </button>
      </div>
    </GardenShell>
  );
}

function writeLocalProfile(profile: GardenProfile) {
  window.localStorage.setItem("potager.location", profile.location);
  window.localStorage.setItem("potager.soilType", profile.type_sol);
  window.localStorage.setItem("potager.irrigation", profile.irrigation);
}

function readLocalProfile(): GardenProfile | null {
  const location = window.localStorage.getItem("potager.location");
  const typeSol = normalizeSoilType(window.localStorage.getItem("potager.soilType"));
  const irrigation = normalizeIrrigation(window.localStorage.getItem("potager.irrigation"));

  if (!location && !typeSol && !irrigation) {
    return null;
  }

  return {
    location: location || "Rennes",
    type_sol: typeSol || "limoneux",
    irrigation: irrigation || "manuel"
  };
}

function normalizeSoilType(value: string | null): SoilType | null {
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

function normalizeIrrigation(value: string | null): IrrigationMode | null {
  if (value === "manuel" || value === "goutte_a_goutte" || value === "automatique" || value === "aucun") {
    return value;
  }
  return null;
}
