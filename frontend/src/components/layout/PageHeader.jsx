export default function PageHeader({ title, subtitle, meta, actions }) {
  return (
    <header className="mb-8 border-b border-trace-border pb-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <h1 className="text-2xl font-semibold tracking-tight text-trace-text">{title}</h1>
          {subtitle ? (
            <p className="mt-2 text-sm leading-relaxed text-trace-muted">{subtitle}</p>
          ) : null}
          {meta ? <div className="mt-3 flex flex-wrap gap-2">{meta}</div> : null}
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
    </header>
  );
}
