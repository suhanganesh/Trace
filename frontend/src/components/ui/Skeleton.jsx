export default function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-md bg-zinc-200/80 ${className}`} aria-hidden="true" />;
}
