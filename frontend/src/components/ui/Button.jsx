export default function Button({
  children,
  variant = 'primary',
  className = '',
  ...props
}) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-ring disabled:opacity-50';
  const variants = {
    primary: 'bg-trace-accent text-white hover:bg-teal-800',
    secondary:
      'border border-trace-border bg-trace-surface text-trace-text hover:bg-zinc-50',
    ghost: 'text-trace-muted hover:bg-zinc-100 hover:text-trace-text',
  };
  return (
    <button type="button" className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
