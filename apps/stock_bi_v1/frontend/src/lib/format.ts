export const formatPercent = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;

export const formatPrice = (value: number) => value.toFixed(2);

export const formatAmount = (value: number) => {
  if (Math.abs(value) >= 1e8) {
    return `${(value / 1e8).toFixed(2)}亿`;
  }
  if (Math.abs(value) >= 1e4) {
    return `${(value / 1e4).toFixed(2)}万`;
  }
  return value.toFixed(0);
};

export const changeToneClass = (value: number) => {
  if (value > 0) {
    return "text-[var(--terminal-up)]";
  }
  if (value < 0) {
    return "text-[var(--terminal-down)]";
  }
  return "text-[var(--terminal-muted)]";
};
