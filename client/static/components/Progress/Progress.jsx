import './Progress.css';

export default function Progress({
  value = 0,
  className = "",
  ...props
}) {
  const clampedValue = Math.min(Math.max(value || 0, 0), 100);

  return (
    <div
      className={`progress ${className}`.trim()}
      role="progressbar"
      aria-valuenow={clampedValue}
      aria-valuemin="0"
      aria-valuemax="100"
      {...props}
    >
      <div
        className="progress-indicator"
        style={{ transform: `translateX(-${100 - clampedValue}%)` }}
      />
    </div>
  );
}
