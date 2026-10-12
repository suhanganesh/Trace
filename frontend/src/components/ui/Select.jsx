export default function Select({ label, id, className = '', children, ...props }) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <label htmlFor={selectId} className={`flex flex-col gap-1 text-sm ${className}`}>
      {label ? <span className="text-xs font-medium text-trace-muted">{label}</span> : null}
      <select
        id={selectId}
        className="focus-ring rounded-md border border-trace-border bg-trace-surface px-2.5 py-1.5 text-sm text-trace-text"
        {...props}
      >
        {children}
      </select>
    </label>
  );
}
