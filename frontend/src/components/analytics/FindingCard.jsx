export default function FindingCard({ category, title, value }) {
  return (
    <article className="rounded-lg border border-trace-border bg-trace-surface p-5">
      {category ? (
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-teal-800">
          {category}
        </p>
      ) : null}
      <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <h3 className="text-base font-semibold text-trace-text">{title}</h3>
        {value ? <p className="tabular-nums text-sm font-medium text-teal-800">{value}</p> : null}
      </div>
    </article>
  );
}
