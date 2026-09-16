interface StatCardProps {
  label: string;
  value: number | string;
  accent?: boolean;
  tone?: "success" | "warning" | "danger" | "info";
  hint?: string;
}

export default function StatCard({ label, value, accent, tone, hint }: StatCardProps) {
  const classes = ["stat-card", accent && "stat-card-accent", tone && `stat-card-${tone}`]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={classes}>
      <div className="stat-card-value tabular-nums">{value}</div>
      <div className="stat-card-label">{label}</div>
      {hint && <div className="stat-card-hint">{hint}</div>}
    </div>
  );
}
