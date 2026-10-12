import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import Overview from './pages/Overview';
import Behavior from './pages/Behavior';
import Products from './pages/Products';
import ProductDetailPage from './pages/ProductDetailPage';
import TimeAnalysis from './pages/TimeAnalysis';
import AnalyticsReport from './pages/AnalyticsReport';
import Dataset from './pages/Dataset';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<Overview />} />
        <Route path="/behavior" element={<Behavior />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/:itemId" element={<ProductDetailPage />} />
        <Route path="/time-analysis" element={<TimeAnalysis />} />
        <Route path="/report" element={<AnalyticsReport />} />
        <Route path="/dataset" element={<Dataset />} />
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Route>
    </Routes>
  );
}
