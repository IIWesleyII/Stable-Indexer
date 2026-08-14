interface MetricCardProps {
  label: string;
  value: string;
  subtitle?: string;
}

export function MetricCard({
  label,
  value,
  subtitle,
}: MetricCardProps) {
  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>

      {subtitle && (
        <span className="metric-subtitle">
          {subtitle}
        </span>
      )}
    </div>
  );
}