import type { ReactNode } from "react";


type TerminalPanelProps = {
  title: string;
  eyebrow?: string;
  actionLabel?: string;
  children: ReactNode;
};


export const TerminalPanel = ({ title, eyebrow, actionLabel, children }: TerminalPanelProps) => (
  <section className="terminal-panel overflow-hidden">
    <header className="mb-5 flex items-start justify-between gap-3 border-b border-[var(--terminal-line)] pb-4">
      <div>
        {eyebrow ? <p className="text-[10px] uppercase tracking-[0.38em] text-[var(--terminal-muted)]">{eyebrow}</p> : null}
        <h2 className="font-display text-[1.95rem] leading-none tracking-[0.08em] text-white">{title}</h2>
      </div>
      {actionLabel ? <span className="rounded-full border border-[var(--terminal-line)] px-3 py-1 text-[10px] uppercase tracking-[0.32em] text-[var(--terminal-muted)]">{actionLabel}</span> : null}
    </header>
    {children}
  </section>
);
