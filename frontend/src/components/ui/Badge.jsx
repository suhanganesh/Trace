export default function Badge({ children, tone = 'neutral', className = '' }) {
  const tones = {
    neutral: 'bg-zinc-100 text-zinc-700',
    accent: 'bg-trace-accent-soft text-teal-900',
    success: 'bg-emerald-50 text-emerald-800',
    warning: 'bg-amber-50 text-amber-900',
  };
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
