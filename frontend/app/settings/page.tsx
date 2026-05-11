"use client";

import { useState } from "react";
import { GardenShell } from "@/components/GardenShell";

type SoilType = "clay" | "sand" | "silt";
type IrrigationMode = "manuel" | "automatique";

const soilOptions: { id: SoilType; icon: string; label: string }[] = [
  { id: "clay", icon: "texture", label: "Clay" },
  { id: "sand", icon: "grain", label: "Sand" },
  { id: "silt", icon: "waves", label: "Silt" }
];

const notifOptions = [
  { key: "watering" as const, label: "Watering Reminders", desc: "Get notified when plants need water." },
  { key: "weather" as const, label: "Weather Alerts", desc: "Frost or heat wave warnings." },
  { key: "harvest" as const, label: "Harvest Ready", desc: "Alerts for ripe produce." }
];

export default function SettingsPage() {
  const [soilType, setSoilType] = useState<SoilType>("clay");
  const [irrigation, setIrrigation] = useState<IrrigationMode>("manuel");
  const [notifications, setNotifications] = useState({ watering: true, weather: false, harvest: true });

  return (
    <GardenShell active="settings">
      <div className="p-container-margin md:p-xl max-w-5xl mx-auto w-full">
        <div className="mb-lg">
          <h1 className="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface mb-xs">
            Settings
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Manage your garden preferences and alerts.
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
                Set your region for accurate weather and planting data.
              </p>
              <div className="relative">
                <select className="w-full appearance-none bg-surface border-b-2 border-primary text-on-surface font-body-md text-body-md py-3 px-4 rounded-t-md shadow-sm focus:outline-none">
                  <option>Paris, Île-de-France</option>
                  <option>Lyon, Auvergne-Rhône-Alpes</option>
                  <option>Marseille, Provence-Alpes-Côte d&apos;Azur</option>
                  <option>Bordeaux, Nouvelle-Aquitaine</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-on-surface-variant">
                  <span className="material-symbols-outlined">arrow_drop_down</span>
                </div>
              </div>
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
                Select the primary soil type in your garden.
              </p>
              <div className="grid grid-cols-3 gap-md">
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
                Choose how you manage watering.
              </p>
              <div className="flex bg-surface-container p-1 rounded-lg">
                {(["manuel", "automatique"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setIrrigation(mode)}
                    className={`flex-1 py-3 text-center rounded-md font-label-lg text-label-lg transition-all ${
                      irrigation === mode
                        ? "bg-surface shadow-sm text-on-surface"
                        : "text-on-surface-variant hover:text-on-surface"
                    }`}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
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
                  <h3 className="font-status-msg text-status-msg text-on-surface">Garden Health</h3>
                  <p className="font-body-md text-body-md text-on-surface-variant mt-2">
                    Your settings help us provide the most accurate recommendations for a thriving garden.
                    Ensure your region and soil type are up to date for the best results.
                  </p>
                </div>
              </div>
              <div className="mt-lg pt-md border-t border-outline-variant">
                <button className="w-full bg-primary hover:bg-primary-container text-on-primary font-label-lg text-label-lg py-4 rounded-lg shadow-sm transition-colors flex items-center justify-center gap-sm min-h-[56px]">
                  <span className="material-symbols-outlined">save</span>
                  Save Preferences
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </GardenShell>
  );
}
