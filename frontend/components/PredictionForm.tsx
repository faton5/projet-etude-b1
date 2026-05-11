"use client";

import { FormEvent, useState } from "react";
import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Send } from "lucide-react";
import {
  createPrediction,
  formatRecommendation,
  type PredictionRequest,
  type PredictionResponse
} from "@/lib/api";

const initialPayload: PredictionRequest = {
  location: "Rennes",
  culture: "tomate",
  saison: "printemps",
  type_sol: "limoneux",
  irrigation: "manuel",
  humidite_sol: 55,
  temp_actuelle: 20,
  temp_min_7j: 8,
  temp_moyenne_7j: 15,
  pluie_7j: true,
  risque_gel_7j: false,
  water_usage: 80
};

export function PredictionForm() {
  const [payload, setPayload] = useState<PredictionRequest>(initialPayload);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    setResult(null);

    try {
      const response = await createPrediction(payload);
      setResult(response);
    } catch {
      setError("Impossible de lancer la prediction. Verifiez que l'API est disponible.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
      <form onSubmit={onSubmit} className="rounded-lg border border-ink/10 bg-white/85 p-6 shadow-soft">
        <h2 className="text-2xl font-bold text-ink">Nouvelle prediction</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <Field label="Localisation">
            <input
              className="input"
              value={payload.location}
              onChange={(event) => setPayload({ ...payload, location: event.target.value })}
            />
          </Field>
          <Field label="Saison">
            <select
              className="input"
              value={payload.saison}
              onChange={(event) =>
                setPayload({ ...payload, saison: event.target.value as PredictionRequest["saison"] })
              }
            >
              <option value="printemps">Printemps</option>
              <option value="ete">Ete</option>
              <option value="automne">Automne</option>
              <option value="hiver">Hiver</option>
            </select>
          </Field>
          <Field label="Type de sol">
            <select
              className="input"
              value={payload.type_sol}
              onChange={(event) =>
                setPayload({ ...payload, type_sol: event.target.value as PredictionRequest["type_sol"] })
              }
            >
              <option value="limoneux">Limoneux</option>
              <option value="argileux">Argileux</option>
              <option value="sableux">Sableux</option>
              <option value="calcaire">Calcaire</option>
              <option value="humifere">Humifere</option>
            </select>
          </Field>
          <Field label="Irrigation">
            <select
              className="input"
              value={payload.irrigation}
              onChange={(event) =>
                setPayload({ ...payload, irrigation: event.target.value as PredictionRequest["irrigation"] })
              }
            >
              <option value="manuel">Manuel</option>
              <option value="goutte_a_goutte">Goutte-a-goutte</option>
              <option value="automatique">Automatique</option>
              <option value="aucun">Aucun</option>
            </select>
          </Field>
          <NumberField label="Humidite du sol (%)" value={payload.humidite_sol} onChange={(value) => setPayload({ ...payload, humidite_sol: value })} />
          <NumberField label="Temperature actuelle (C)" value={payload.temp_actuelle} onChange={(value) => setPayload({ ...payload, temp_actuelle: value })} />
          <NumberField label="Temperature minimale 7j (C)" value={payload.temp_min_7j} onChange={(value) => setPayload({ ...payload, temp_min_7j: value })} />
          <NumberField label="Temperature moyenne 7j (C)" value={payload.temp_moyenne_7j} onChange={(value) => setPayload({ ...payload, temp_moyenne_7j: value })} />
          <NumberField label="Usage eau estime" value={payload.water_usage} onChange={(value) => setPayload({ ...payload, water_usage: value })} />
          <div className="grid gap-3 rounded-md bg-cream p-4">
            <label className="flex items-center justify-between gap-4 font-semibold text-ink">
              Pluie prevue
              <input
                type="checkbox"
                checked={payload.pluie_7j}
                onChange={(event) => setPayload({ ...payload, pluie_7j: event.target.checked })}
                className="h-5 w-5 accent-leaf"
              />
            </label>
            <label className="flex items-center justify-between gap-4 font-semibold text-ink">
              Risque de gel
              <input
                type="checkbox"
                checked={payload.risque_gel_7j}
                onChange={(event) => setPayload({ ...payload, risque_gel_7j: event.target.checked })}
                className="h-5 w-5 accent-tomato"
              />
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={pending}
          className="mt-6 inline-flex items-center gap-2 rounded-md bg-tomato px-4 py-3 font-semibold text-white transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Send size={18} aria-hidden="true" />
          {pending ? "Analyse en cours" : "Analyser la plantation"}
        </button>
      </form>

      <aside className="rounded-lg border border-ink/10 bg-cream p-6 shadow-soft">
        <h2 className="text-2xl font-bold text-ink">Resultat</h2>
        {result && (
          <div className="mt-6">
            <CheckCircle2 className="text-leaf" size={34} aria-hidden="true" />
            <p className="mt-4 text-4xl font-bold text-tomato">
              {formatRecommendation(result.recommandation)}
            </p>
            <p className="mt-3 text-lg text-ink/75">
              Confiance : {Math.round(result.score_confiance * 100)} %
            </p>
            <p className="mt-4 leading-7 text-ink/75">{result.explication}</p>
          </div>
        )}
        {error && (
          <p className="mt-6 flex items-start gap-2 rounded-md bg-white p-4 font-semibold text-tomato">
            <AlertTriangle size={18} aria-hidden="true" />
            {error}
          </p>
        )}
        {!result && !error && (
          <p className="mt-6 leading-7 text-ink/70">
            Remplissez les conditions du potager pour obtenir une recommandation.
          </p>
        )}
      </aside>
    </section>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="grid gap-2">
      <span className="font-semibold text-ink">{label}</span>
      {children}
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <Field label={label}>
      <input
        type="number"
        className="input"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </Field>
  );
}
