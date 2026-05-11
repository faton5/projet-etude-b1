"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Activity, Brain, Database, Server } from "lucide-react";
import { getHealth, getModelInfo, type HealthResponse, type ModelInfoResponse } from "@/lib/api";

export function SystemStatusPanel() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [model, setModel] = useState<ModelInfoResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [healthResponse, modelResponse] = await Promise.all([getHealth(), getModelInfo()]);
        if (!cancelled) {
          setHealth(healthResponse);
          setModel(modelResponse);
          setError("");
        }
      } catch {
        if (!cancelled) {
          setError("API indisponible");
        }
      }
    }

    load();
    const interval = setInterval(load, 10000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <section className="rounded-lg border border-ink/10 bg-white/85 p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Activity className={error ? "text-tomato" : "text-leaf"} aria-hidden="true" />
          <h2 className="text-xl font-bold text-ink">Etat systeme</h2>
        </div>
        {health?.demo_mode && (
          <span className="rounded-md bg-cream px-3 py-1 text-sm font-semibold text-soil">
            Mode demo
          </span>
        )}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <StatusItem icon={<Server size={18} aria-hidden="true" />} label="API" status={error ? "error" : "ok"} />
        <StatusItem
          icon={<Database size={18} aria-hidden="true" />}
          label="SQLite"
          status={health?.database === "ok" ? "ok" : "warning"}
        />
        <StatusItem
          icon={<Brain size={18} aria-hidden="true" />}
          label="Modele"
          status={health?.model === "loaded" ? "ok" : "warning"}
          detail={model ? `v${model.version}` : undefined}
        />
        <StatusItem
          icon={<Activity size={18} aria-hidden="true" />}
          label="MQTT"
          status={health?.mqtt === "connected" ? "ok" : health?.mqtt === "demo" ? "warning" : "error"}
          detail={formatMqtt(health?.mqtt)}
        />
      </div>
    </section>
  );
}

function StatusItem({
  icon,
  label,
  status,
  detail
}: {
  icon: ReactNode;
  label: string;
  status: "ok" | "warning" | "error";
  detail?: string;
}) {
  const styles = {
    ok: "bg-leaf/10 text-leaf",
    warning: "bg-cream text-soil",
    error: "bg-tomato/10 text-tomato"
  }[status];
  const dot = {
    ok: "bg-leaf",
    warning: "bg-soil",
    error: "bg-tomato"
  }[status];

  return (
    <div className="rounded-md bg-cream/80 p-4 transition duration-300 hover:bg-cream">
      <div className={`inline-flex items-center gap-2 rounded-md px-2 py-1 text-sm font-semibold ${styles}`}>
        <span className={`h-2 w-2 rounded-full ${dot}`} />
        {icon}
        {label}
      </div>
      <p className="mt-3 text-sm font-semibold text-ink/70">{detail ?? label}</p>
    </div>
  );
}

function formatMqtt(value?: string) {
  return {
    connected: "connecte",
    reconnecting: "reconnexion",
    disabled: "desactive",
    demo: "demo"
  }[value ?? "reconnecting"];
}
