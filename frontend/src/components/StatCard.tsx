interface StatCardProps {
  label: string;
  value: number | string;
  accent?: boolean;
  tone?: "danger";
}

export default function StatCard({ label, value, accent, tone }: StatCardProps) {
  const classes = ["stat-card", accent && "stat-card-accent", tone && `stat-card-${tone}`]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={classes}>
      <div className="stat-card-value">{value}</div>
      <div className="stat-card-label">{label}</div>
    </div>
  );
}
