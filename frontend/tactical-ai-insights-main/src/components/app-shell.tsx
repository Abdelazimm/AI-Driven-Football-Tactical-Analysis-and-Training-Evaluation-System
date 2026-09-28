import { Link, useRouterState } from "@tanstack/react-router";
import { BarChart3, Beaker, FlaskConical, LayoutDashboard, Menu, Plus, ShieldCheck, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analysis/new", label: "New Analysis", icon: Plus },
  { to: "/comparisons", label: "Comparisons", icon: BarChart3 },
  { to: "/showcase", label: "Validated Showcase", icon: ShieldCheck },
  { to: "/research", label: "Research / Methodology", icon: FlaskConical },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const path = useRouterState({ select: (s) => s.location.pathname });
  return <div className="min-h-screen bg-background text-foreground">
    <header className="sticky top-0 z-50 border-b border-border bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex h-18 max-w-[1600px] items-center gap-4 px-4 lg:px-8">
        <Link to="/" className="flex min-w-0 items-center gap-2 sm:gap-3" onClick={() => setOpen(false)}>
          <span className="flex shrink-0 items-center gap-1.5 sm:gap-2">
            <img src="/branding/project-logo.svg" alt="AI-Driven Football Tactical Analysis and Training Evaluation System project logo" className="h-11 w-10 object-contain brightness-[2.3] sm:h-12 sm:w-11" />
            <img src="/branding/university-logo.svg" alt="University logo" className="h-10 w-10 object-contain sm:h-11 sm:w-11" />
          </span>
          <span className="min-w-0 max-w-[11rem] sm:max-w-[19rem] xl:max-w-[18rem]">
            <span className="block text-[10px] font-extrabold uppercase leading-tight sm:text-xs">AI-Driven Football Tactical Analysis and Training Evaluation System</span>
            <span className="mt-0.5 hidden font-mono text-[10px] uppercase text-ai sm:block">Final Year Project</span>
          </span>
        </Link>
        <nav className="ml-auto hidden items-center gap-1 xl:flex">
          {nav.map((item) => <Link key={item.to} to={item.to} className={`rounded-md px-3 py-2 text-xs font-semibold transition-colors ${path === item.to ? "bg-accent text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground"}`}>{item.label}</Link>)}
        </nav>
        <div className="ml-auto hidden items-center gap-2 xl:ml-3 xl:flex"><span className="h-2 w-2 rounded-full bg-primary"/><span className="font-mono text-[10px] text-muted-foreground">LOCAL PRESENTATION</span></div>
        <Button className="ml-auto xl:hidden" variant="ghost" size="icon" aria-label="Toggle navigation" onClick={() => setOpen(!open)}>{open ? <X/> : <Menu/>}</Button>
      </div>
      {open && <nav className="border-t border-border bg-background px-4 py-3 xl:hidden">{nav.map((item) => { const Icon=item.icon; return <Link key={item.to} to={item.to} onClick={() => setOpen(false)} className="flex items-center gap-3 border-b border-border/60 py-3 text-sm text-muted-foreground last:border-0"><Icon className="h-4 w-4 text-ai"/>{item.label}</Link>})}</nav>}
    </header>
    <main>{children}</main>
    <footer className="border-t border-border px-4 py-6"><div className="mx-auto flex max-w-[1500px] items-center justify-between gap-4 text-xs text-muted-foreground"><span>Final Year Project · Scientific evidence, responsibly presented.</span><Beaker className="h-4 w-4 text-ai"/></div></footer>
  </div>;
}
