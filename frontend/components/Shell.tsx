import Link from "next/link";
import type { ReactNode } from "react";
import { BarChart3, History, Settings, Sprout } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/predict", label: "Prediction", icon: Sprout },
  { href: "/history", label: "Historique", icon: History },
  { href: "/settings", label: "Reglages", icon: Settings }
];

export function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="dashboard-grid min-h-screen">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-ink/10 pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tomato">
              V0 Potager EHPAD
            </p>
            <h1 className="mt-1 text-3xl font-bold text-ink sm:text-4xl">
              Tomates sous surveillance
            </h1>
          </div>
          <nav className="flex flex-wrap gap-2">
            {links.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="inline-flex items-center gap-2 rounded-md border border-ink/10 bg-white/75 px-3 py-2 text-sm font-semibold text-ink shadow-sm transition hover:border-leaf hover:text-leaf"
                >
                  <Icon size={16} aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </header>
        {children}
      </div>
    </main>
  );
}
