import { useCallback, useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { fetchHealth } from '../../api/health';
import { NAV_ITEMS } from '../../utils/constants';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [refreshToken, setRefreshToken] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const location = useLocation();

  const loadHealth = useCallback(async () => {
    setHealthLoading(true);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      setHealth({ status: 'degraded', database: 'disconnected', database_name: '—' });
    } finally {
      setHealthLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();
  }, [loadHealth, refreshToken]);

  const navItem = NAV_ITEMS.find((item) => location.pathname.startsWith(item.to));
  const title = navItem?.label || 'Trace';

  const handleRefresh = () => {
    setRefreshing(true);
    setRefreshToken((value) => value + 1);
    setTimeout(() => setRefreshing(false), 400);
  };

  return (
    <div className="flex min-h-screen bg-trace-bg">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} health={health} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          title={title}
          breadcrumb="Trace / Analytics"
          health={health}
          healthLoading={healthLoading}
          onMenuClick={() => setSidebarOpen(true)}
          onRefresh={handleRefresh}
          refreshing={refreshing}
        />
        <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet context={{ refreshToken, health }} />
        </main>
      </div>
    </div>
  );
}
