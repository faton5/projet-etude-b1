import { MapPin, Settings } from "lucide-react";
import { Shell } from "@/components/Shell";

export default function SettingsPage() {
  return (
    <Shell>
      <section className="grid gap-5 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-lg border border-ink/10 bg-white/85 p-6 shadow-soft">
          <div className="flex items-center gap-3">
            <Settings className="text-leaf" aria-hidden="true" />
            <h2 className="text-2xl font-bold text-ink">Reglages V0</h2>
          </div>
          <div className="mt-6 grid gap-4">
            <label className="grid gap-2">
              <span className="font-semibold text-ink">Localisation par defaut</span>
              <input className="rounded-md border border-ink/15 bg-white px-3 py-2" defaultValue="Rennes" />
            </label>
            <label className="grid gap-2">
              <span className="font-semibold text-ink">Type de sol</span>
              <select className="rounded-md border border-ink/15 bg-white px-3 py-2" defaultValue="limoneux">
                <option value="limoneux">Limoneux</option>
                <option value="argileux">Argileux</option>
                <option value="sableux">Sableux</option>
                <option value="calcaire">Calcaire</option>
                <option value="humifere">Humifere</option>
              </select>
            </label>
            <label className="grid gap-2">
              <span className="font-semibold text-ink">Irrigation</span>
              <select className="rounded-md border border-ink/15 bg-white px-3 py-2" defaultValue="manuel">
                <option value="manuel">Manuel</option>
                <option value="goutte_a_goutte">Goutte-a-goutte</option>
                <option value="automatique">Automatique</option>
                <option value="aucun">Aucun</option>
              </select>
            </label>
          </div>
        </div>
        <div className="rounded-lg border border-ink/10 bg-cream p-6 shadow-soft">
          <MapPin className="text-tomato" aria-hidden="true" />
          <h2 className="mt-4 text-2xl font-bold text-ink">Configuration locale</h2>
          <p className="mt-3 leading-7 text-ink/70">
            Ces champs preparent les reglages persistants. Dans cette V0, les valeurs
            importantes sont saisies dans le formulaire de prediction.
          </p>
        </div>
      </section>
    </Shell>
  );
}
