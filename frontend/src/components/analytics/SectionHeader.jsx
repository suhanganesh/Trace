import Tooltip from '../ui/Tooltip';
import { Info } from 'lucide-react';

export default function SectionHeader({ title, description, hint }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-trace-text">{title}</h2>
        {description ? <p className="mt-1 text-sm text-trace-muted">{description}</p> : null}
      </div>
      {hint ? (
        <Tooltip label={hint}>
          <button
            type="button"
            className="rounded p-1 text-trace-muted hover:bg-zinc-100 focus-ring"
            aria-label="Methodology information"
          >
            <Info size={15} />
          </button>
        </Tooltip>
      ) : null}
    </div>
  );
}
