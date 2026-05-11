import { Shell } from "@/components/Shell";
import { formatRecommendation, getHistory, type HistoryItem } from "@/lib/api";

export default async function HistoryPage() {
  let history: HistoryItem[] = [];
  let error = "";

  try {
    history = await getHistory(100);
  } catch {
    error = "Historique indisponible. Verifiez que l'API est lancee.";
  }

  return (
    <Shell>
      <section className="rounded-lg border border-ink/10 bg-white/85 p-6 shadow-soft">
        <h2 className="text-2xl font-bold text-ink">Historique des predictions</h2>
        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-left">
            <thead>
              <tr className="border-b border-ink/10 text-sm uppercase tracking-[0.12em] text-ink/55">
                <th className="py-3 pr-4">Date</th>
                <th className="py-3 pr-4">Lieu</th>
                <th className="py-3 pr-4">Decision</th>
                <th className="py-3 pr-4">Confiance</th>
                <th className="py-3 pr-4">Temp. min</th>
                <th className="py-3 pr-4">Gel</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.id} className="border-b border-ink/10 text-ink">
                  <td className="py-3 pr-4">
                    {new Date(item.created_at).toLocaleString("fr-FR")}
                  </td>
                  <td className="py-3 pr-4">{item.request.location}</td>
                  <td className="py-3 pr-4 font-bold">
                    {formatRecommendation(item.recommandation)}
                  </td>
                  <td className="py-3 pr-4">{Math.round(item.score_confiance * 100)} %</td>
                  <td className="py-3 pr-4">{item.request.temp_min_7j} C</td>
                  <td className="py-3 pr-4">{item.request.risque_gel_7j ? "Oui" : "Non"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!history.length && (
          <p className="mt-5 rounded-md bg-cream p-4 text-ink/70">
            {error || "Aucune prediction enregistree."}
          </p>
        )}
      </section>
    </Shell>
  );
}
