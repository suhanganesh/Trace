export default function Tooltip({ label, children }) {
  return (
    <span className="group relative inline-flex">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 hidden w-max max-w-xs -translate-x-1/2 rounded-md border border-trace-border bg-trace-surface px-2 py-1 text-xs text-trace-muted shadow-trace group-hover:block group-focus-within:block"
      >
        {label}
      </span>
    </span>
  );
}
