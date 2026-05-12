import Link from "next/link";
import type { ReactNode } from "react";

export function GardenShell({
  children,
  active
}: {
  children: ReactNode;
  active: "home" | "settings";
}) {
  return (
    <div className="bg-background text-on-background min-h-screen flex flex-col md:flex-row">
      {/* SideNavBar desktop */}
      <nav className="hidden md:flex flex-col h-screen py-xl px-md gap-lg bg-surface-container-low shadow-sm fixed top-0 left-0 w-64 z-10">
        <div className="mb-lg">
          <h1 className="font-headline-lg text-headline-lg text-primary">Potager EHPAD</h1>
          <p className="font-body-md text-body-md text-on-surface-variant opacity-70">Jardin des tomates</p>
        </div>
        <ul className="flex flex-col gap-sm">
          <li>
            <Link
              href="/dashboard"
              className={`flex items-center gap-sm py-sm px-base rounded-lg transition-colors ${
                active === "home"
                  ? "bg-surface-variant text-primary font-bold border-l-4 border-primary"
                  : "text-on-surface-variant opacity-70 hover:bg-surface-variant"
              }`}
            >
              <span
                className="material-symbols-outlined"
                style={active === "home" ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                home
              </span>
              <span className="font-label-lg text-label-lg">Accueil</span>
            </Link>
          </li>
          <li>
            <Link
              href="/settings"
              className={`flex items-center gap-sm py-sm px-base rounded-lg transition-colors ${
                active === "settings"
                  ? "bg-surface-variant text-primary font-bold border-l-4 border-primary"
                  : "text-on-surface-variant opacity-70 hover:bg-surface-variant"
              }`}
            >
              <span
                className="material-symbols-outlined"
                style={active === "settings" ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                settings
              </span>
              <span className="font-label-lg text-label-lg">Réglages</span>
            </Link>
          </li>
        </ul>
        <div className="mt-auto flex items-center gap-sm pt-md border-t border-surface-variant">
          <span className="material-symbols-outlined text-[32px] text-tertiary">account_circle</span>
          <span className="font-label-lg text-label-lg">Profil équipe</span>
        </div>
      </nav>

      {/* TopAppBar mobile */}
      <header className="flex justify-between items-center w-full px-container-margin py-md bg-background sticky top-0 z-40 md:hidden">
        <div className="font-headline-md text-headline-md font-bold text-primary">Potager EHPAD</div>
        <button className="text-on-surface-variant opacity-60 hover:opacity-100 transition-opacity">
          <span className="material-symbols-outlined text-[28px]">person</span>
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 md:ml-64 flex flex-col pb-16 md:pb-0">
        {children}
      </main>

      {/* BottomNavBar mobile */}
      <nav className="md:hidden fixed bottom-0 w-full bg-surface border-t border-surface-variant z-50 flex justify-around items-center py-2 px-4 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
        <Link
          href="/dashboard"
          className={`flex flex-col items-center p-2 transition-opacity ${
            active === "home" ? "text-primary font-bold" : "text-on-surface-variant opacity-60 hover:opacity-100"
          }`}
        >
          <span
            className="material-symbols-outlined"
            style={active === "home" ? { fontVariationSettings: "'FILL' 1" } : undefined}
          >
            home
          </span>
          <span className="text-xs font-label-lg mt-1">Accueil</span>
        </Link>
        <Link
          href="/settings"
          className={`flex flex-col items-center p-2 transition-opacity ${
            active === "settings" ? "text-primary font-bold" : "text-on-surface-variant opacity-60 hover:opacity-100"
          }`}
        >
          <span
            className="material-symbols-outlined"
            style={active === "settings" ? { fontVariationSettings: "'FILL' 1" } : undefined}
          >
            settings
          </span>
          <span className="text-xs font-label-lg mt-1">Réglages</span>
        </Link>
      </nav>
    </div>
  );
}
