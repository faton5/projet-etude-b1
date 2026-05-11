import { GardenShell } from "@/components/GardenShell";

const kpis = [
  { icon: "device_thermostat", label: "Température", value: "22°C", span: false },
  { icon: "water_drop", label: "Humidité sol", value: "45%", span: false },
  { icon: "rainy", label: "Pluie", value: "Aucune", span: false },
  { icon: "ac_unit", label: "Risque gel", value: "Faible", span: false },
  { icon: "sprinkler", label: "Irrigation", value: "Auto", span: true }
];

export default function DashboardPage() {
  return (
    <GardenShell active="home">
      <div className="flex-1 px-container-margin py-lg max-w-7xl mx-auto w-full flex flex-col gap-xl">

        {/* Status Card */}
        <section className="bg-primary-container text-on-primary-container rounded-3xl p-xl shadow-sm border-l-8 border-primary flex flex-col md:flex-row items-start md:items-center justify-between gap-lg relative overflow-hidden">
          <span
            className="material-symbols-outlined absolute -right-8 -top-8 text-[200px] opacity-10"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            eco
          </span>
          <div className="flex flex-col gap-sm z-10">
            <h2 className="font-display-lg text-display-lg-mobile md:text-display-lg font-bold">
              Tout va bien pour les tomates aujourd&apos;hui.
            </h2>
            <p className="font-status-msg text-status-msg-mobile md:text-status-msg opacity-90">
              Jardin Sud - Zone 2
            </p>
          </div>
          <button className="z-10 bg-surface-bright text-primary px-lg py-sm rounded-full font-label-lg text-label-lg h-[56px] shadow-sm hover:bg-surface-variant transition-colors whitespace-nowrap">
            Voir pourquoi
          </button>
        </section>

        {/* Recommendation */}
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
              Attendre avant d&apos;arroser.
            </p>
            <p className="font-body-lg text-body-lg text-on-surface-variant">
              Température idéale pour la croissance.
            </p>
          </div>
        </section>

        {/* KPI Bento Grid */}
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

        {/* Humidity Trend */}
        <section className="bg-surface-container-lowest rounded-3xl p-xl shadow-sm border border-surface-variant">
          <h3 className="font-headline-lg text-headline-lg text-on-surface mb-lg">
            Tendance Humidité
          </h3>
          <div className="w-full h-[200px] relative mt-md">
            <div className="absolute inset-0 flex flex-col justify-between opacity-10">
              <div className="border-b-2 border-on-surface w-full" />
              <div className="border-b-2 border-on-surface w-full" />
              <div className="border-b-2 border-on-surface w-full" />
            </div>
            <svg className="w-full h-full" viewBox="0 0 1000 200" preserveAspectRatio="none">
              <defs>
                <linearGradient id="humidity-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#334f2b" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#334f2b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <path
                d="M0,180 C200,180 300,100 500,120 C700,140 800,40 1000,50 L1000,200 L0,200 Z"
                fill="url(#humidity-gradient)"
                opacity={0.3}
              />
              <path
                d="M0,180 C200,180 300,100 500,120 C700,140 800,40 1000,50"
                fill="none"
                stroke="#334f2b"
                strokeLinecap="round"
                strokeWidth={4}
              />
              <circle cx={500} cy={120} r={8} fill="#334f2b" />
              <circle cx={1000} cy={50} r={8} fill="#334f2b" />
            </svg>
            <div className="flex justify-between mt-sm font-label-lg text-label-lg text-on-surface-variant opacity-70 px-sm">
              <span>Matin</span>
              <span>Midi</span>
              <span>Maintenant</span>
            </div>
          </div>
        </section>

      </div>
    </GardenShell>
  );
}
