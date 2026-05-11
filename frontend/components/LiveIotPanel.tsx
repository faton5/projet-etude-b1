"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Droplets, Radio, Waves } from "lucide-react";
import { getIotLive, getIotWebSocketUrl, type IotLiveResponse } from "@/lib/api";

export function LiveIotPanel() {
  const [data, setData] = useState<IotLiveResponse | null>(null);
  const [status, setStatus] = useState<"connecting" | "live" | "fallback" | "error">("connecting");

  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | null = null;
    let fallbackInterval: ReturnType<typeof setInterval> | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

    async function loadFallback() {
      try {
        const response = await getIotLive();
        if (!cancelled) {
          setData(response);
          setStatus("fallback");
        }
      } catch {
        if (!cancelled) {
          setStatus("error");
        }
      }
    }

    function openSocket() {
      if (cancelled) {
        return;
      }
      setStatus("connecting");
      socket = new WebSocket(getIotWebSocketUrl());
      socket.onmessage = (event) => {
        setData(JSON.parse(event.data));
        setStatus("live");
      };
      socket.onerror = () => {
        socket?.close();
      };
      socket.onclose = () => {
        if (!cancelled) {
          loadFallback();
          reconnectTimeout = setTimeout(openSocket, 4000);
        }
      };
    }

    try {
      openSocket();
    } catch {
      loadFallback();
      fallbackInterval = setInterval(loadFallback, 5000);
    }

    return () => {
      cancelled = true;
      socket?.close();
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (fallbackInterval) {
        clearInterval(fallbackInterval);
      }
    };
  }, []);

  const lastUpdate = data?.last_update
    ? new Date(data.last_update).toLocaleTimeString("fr-FR")
    : "En attente";

  return (
    <section className="rounded-lg border border-ink/10 bg-white/85 p-5 shadow-soft">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Radio className={data?.mqtt_connected ? "text-leaf" : "text-tomato"} aria-hidden="true" />
            <h2 className="text-xl font-bold text-ink">IoT live</h2>
          </div>
          <p className="mt-2 text-sm text-ink/65">
            MQTT {formatStatus(data?.mqtt_status)} - {status === "live" ? "WebSocket" : "HTTP"} - {lastUpdate}
          </p>
        </div>
        <span className={`inline-flex w-fit rounded-md px-3 py-1 text-sm font-semibold ${statusTone(data?.mqtt_status)}`}>
          {data?.demo ? "demo" : data?.farm_id ?? "farm_1"}
        </span>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <Metric
          icon={<Waves size={18} aria-hidden="true" />}
          label="Humidite sol"
          value={data?.soil_humidity != null ? `${data.soil_humidity} %` : "Aucune donnee"}
        />
        <Metric
          icon={<Droplets size={18} aria-hidden="true" />}
          label="Usage eau"
          value={data?.water_usage != null ? `${data.water_usage} L/j` : "Aucune donnee"}
        />
        <Metric
          icon={<Radio size={18} aria-hidden="true" />}
          label="Irrigation"
          value={data?.irrigation ? formatIrrigation(data.irrigation) : "Aucune donnee"}
        />
      </div>
    </section>
  );
}

function Metric({
  icon,
  label,
  value
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md bg-cream p-4 transition duration-300 hover:bg-white">
      <div className="flex items-center gap-2 text-sm font-semibold text-ink/60">
        {icon}
        {label}
      </div>
      <p className="mt-2 text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}

function formatIrrigation(value: string) {
  return {
    manuel: "Manuel",
    goutte_a_goutte: "Goutte-a-goutte",
    automatique: "Automatique",
    aucun: "Aucun"
  }[value] ?? value;
}

function formatStatus(value?: IotLiveResponse["mqtt_status"]) {
  return {
    connected: "connecte",
    reconnecting: "reconnexion",
    disabled: "desactive",
    demo: "demo"
  }[value ?? "reconnecting"];
}

function statusTone(value?: IotLiveResponse["mqtt_status"]) {
  return {
    connected: "bg-leaf/10 text-leaf",
    reconnecting: "bg-cream text-soil",
    disabled: "bg-tomato/10 text-tomato",
    demo: "bg-cream text-soil"
  }[value ?? "reconnecting"];
}
