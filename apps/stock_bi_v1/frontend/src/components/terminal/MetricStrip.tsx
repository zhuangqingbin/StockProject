type MetricStripProps = {
  items: Array<{ label: string; value: string; tone?: "up" | "down" | "neutral" }>;
};


export const MetricStrip = ({ items }: MetricStripProps) => (
  <div className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
    {items.map((item) => (
      <div key={item.label} className="rounded-[20px] border border-[var(--terminal-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] px-4 py-4 shadow-[0_18px_40px_rgba(0,0,0,0.16)]">
        <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--terminal-muted)]">{item.label}</p>
        <p
          className={[
            "mt-2 font-display text-xl tracking-[0.06em]",
            item.tone === "up"
              ? "text-[var(--terminal-up)]"
              : item.tone === "down"
                ? "text-[var(--terminal-down)]"
                : "text-white",
          ].join(" ")}
        >
          {item.value}
        </p>
      </div>
    ))}
  </div>
);
