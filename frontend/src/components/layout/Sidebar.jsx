import { NavLink } from 'react-router-dom';
import {
  Clock,
  Database,
  FileBarChart,
  LayoutDashboard,
  Package,
  Users,
  X,
} from 'lucide-react';
import { APP_NAME, NAV_ITEMS } from '../../utils/constants';

const ICONS = {
  LayoutDashboard,
  Users,
  Package,
  Clock,
  FileBarChart,
  Database,
};

export default function Sidebar({ open, onClose, health }) {
  return (
    <>
      <div
        className={`fixed inset-0 z-40 bg-zinc-900/20 backdrop-blur-[1px] transition-opacity lg:hidden ${
          open ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-trace-border bg-trace-surface transition-transform lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Primary navigation"
      >
        <div className="flex items-center justify-between border-b border-trace-border px-4 py-4">
          <div className="flex items-center gap-2.5">
            <img src="/trace-mark.svg" alt="" className="h-8 w-8 rounded-md" />
            <div>
              <p className="text-sm font-semibold tracking-[0.18em] text-trace-text">{APP_NAME}</p>
              <p className="text-[11px] text-trace-muted">E-commerce intelligence</p>
            </div>
          </div>
          <button
            type="button"
            className="rounded-md p-1 text-trace-muted hover:bg-zinc-100 lg:hidden focus-ring"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-2 py-4">
          {NAV_ITEMS.map((item) => {
            const Icon = ICONS[item.icon];
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-ring ${
                    isActive
                      ? 'bg-teal-50 text-teal-900'
                      : 'text-trace-muted hover:bg-zinc-50 hover:text-trace-text'
                  }`
                }
              >
                <Icon size={16} strokeWidth={1.75} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="border-t border-trace-border px-4 py-4 text-xs text-trace-muted">
          <p className="font-medium text-trace-text">System</p>
          <p className="mt-1">
            API:{' '}
            <span className={health?.database === 'connected' ? 'text-teal-700' : 'text-amber-700'}>
              {health?.database === 'connected' ? 'Connected' : 'Unavailable'}
            </span>
          </p>
          {health?.database_name ? <p className="mt-0.5 truncate">{health.database_name}</p> : null}
        </div>
      </aside>
    </>
  );
}
