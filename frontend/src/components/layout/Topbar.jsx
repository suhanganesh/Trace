import { Menu, RefreshCw } from 'lucide-react';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

export default function Topbar({
  title,
  breadcrumb,
  dateRange,
  health,
  healthLoading,
  onMenuClick,
  onRefresh,
  refreshing,
}) {
  const connected = health?.database === 'connected';

  return (
    <div className="sticky top-0 z-30 border-b border-trace-border bg-trace-bg/90 backdrop-blur-sm">
      <div className="flex items-center justify-between gap-4 px-4 py-3 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            className="rounded-md p-1.5 text-trace-muted hover:bg-zinc-100 lg:hidden focus-ring"
            onClick={onMenuClick}
            aria-label="Open navigation"
          >
            <Menu size={18} />
          </button>
          <div className="min-w-0">
            {breadcrumb ? (
              <p className="truncate text-xs text-trace-muted">{breadcrumb}</p>
            ) : null}
            <p className="truncate text-sm font-medium text-trace-text">{title}</p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {dateRange ? (
            <span className="hidden text-xs text-trace-muted md:inline">{dateRange}</span>
          ) : null}
          {healthLoading ? (
            <Badge tone="neutral">Checking…</Badge>
          ) : (
            <Badge tone={connected ? 'success' : 'warning'}>
              {connected ? 'Connected' : 'Disconnected'}
            </Badge>
          )}
          {onRefresh ? (
            <Button
              variant="ghost"
              className="px-2"
              onClick={onRefresh}
              disabled={refreshing}
              aria-label="Refresh page data"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
