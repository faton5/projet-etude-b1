import Link from "next/link";
import { AlertTriangle, CheckCircle2, Leaf, ThermometerSun } from "lucide-react";
import { LiveIotPanel } from "@/components/LiveIotPanel";
import { Shell } from "@/components/Shell";
import { StatCard } from "@/components/StatCard";
import { SystemStatusPanel } from "@/components/SystemStatusPanel";
import { formatRecommendation, getHistory, type HistoryItem } from "@/lib/api";

export default async function DashboardPage() {
  let history: HistoryItem[] = [];
  let error = "";

  try {
    history = await getHistory(50);
  } catch {
    error = "API indisponible. Lancez le backend pour afficher les donnees.";
  }

  const latest = history[0];
  const total = history.length;
  const viable = history.filter((item) => item.recommandation === "viable").length;
  const waiting = history.filter((item) => item.recommandation === "attendre").length;
  const blocked = history.filter((item) => item.recommandation === "non_viable").length;

  return (
    <Shell>
      <section className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <div className="rounded-lg border border-ink/10 bg-white/85 p-6 shadow-soft">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-leaf">
                Culture analysee
              </p>
              <h2 className="mt-2 text-4xl font-bold text-ink">Tomate</h2>
            </div>
            <Leaf className="text-leaf" size={36} aria-hidden="true" />
          </div>

          {latest ? (
            <div className="mt-8 grid gap-5 md:grid-cols-[1fr_1.2fr]">
              <div>
                <p className="text-sm font-semibold text-ink/60">Recommandation</p>
                <p className="mt-2 text-5xl font-bold text-tomato">
                  {formatRecommendation(latest.recommandation)}
                </p>
                <p className="mt-3 text-lg text-ink/75">
                  Confiance : {Math.round(latest.score_confiance * 100)} %
                </p>
              </div>
              <div className="rounded-md bg-cream p-4">
                <p className="font-semibold text-ink">Raison</p>
                <p className="mt-2 leading-7 text-ink/75">{latest.explication}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {latest.facteurs_importants.map((factor) => (
                    <span
                      key={factor}
                      className="rounded-md bg-white px-2.5 py-1 text-sm font-semibold text-soil"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-8 rounded-md bg-cream p-5 text-ink/75">
              {error || "Aucune prediction pour le moment."}
            </div>
          )}

          <Link
            href="/predict"
            className="mt-6 inline-flex items-center gap-2 rounded-md bg-leaf px-4 py-3 font-semibold text-white transition hover:bg-ink"
          >
            <CheckCircle2 size={18} aria-hidden="true" />
            Lancer une prediction
          </Link>
        </div>

        <div className="grid gap-4">
          <StatCard label="Total predictions" value={`${total}`} tone="soil" />
          <StatCard label="Viables" value={`${viable}`} tone="leaf" />
          <StatCard label="A attendre" value={`${waiting}`} />
          <StatCard label="Non viables" value={`${blocked}`} tone="tomato" />
        </div>
      </section>

      {latest && (
        <section className="grid gap-4 md:grid-cols-3">
          <StatCard
            label="Temperature minimale"
            value={`${latest.request.temp_min_7j} C`}
            tone="tomato"
          />
          <StatCard
            label="Risque de gel"
            value={latest.request.risque_gel_7j ? "Oui" : "Non"}
            tone={latest.request.risque_gel_7j ? "tomato" : "leaf"}
          />
          <StatCard
            label="Humidite du sol"
            value={`${latest.request.humidite_sol} %`}
            tone="leaf"
          />
        </section>
      )}

      <SystemStatusPanel />

      <LiveIotPanel />

      <section className="rounded-lg border border-ink/10 bg-white/80 p-5 shadow-soft">
        <div className="flex items-center gap-3">
          <ThermometerSun className="text-tomato" aria-hidden="true" />
          <h2 className="text-xl font-bold text-ink">Decision V0</h2>
        </div>
        <p className="mt-3 max-w-3xl leading-7 text-ink/70">
          Cette premiere version utilise des regles metier proches du futur modele XGBoost :
          gel, temperature minimale, saison, humidite et irrigation.
        </p>
        {error && (
          <p className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-tomato">
            <AlertTriangle size={16} aria-hidden="true" />
            {error}
          </p>
        )}
      </section>
    </Shell>
  );
}
