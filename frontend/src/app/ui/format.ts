export function fmtPct(x: unknown, digits = 1): string {
  const n = typeof x === "number" ? x : Number(x);
  if (!Number.isFinite(n)) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

export function fmtNum(x: unknown, digits = 2): string {
  const n = typeof x === "number" ? x : Number(x);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

export function fmtDateTimeIso(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

export function fmtDurationSec(sec: number | null | undefined): string {
  if (sec == null) return "—";
  const s = Math.max(0, sec);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  return `${h}h`;
}

