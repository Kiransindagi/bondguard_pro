import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { Overview } from './pages/Overview';
import { System } from './pages/System';
import { DataMonitor } from './pages/DataMonitor';
import { Portfolio } from './pages/Portfolio';
import { BondExplorer } from './pages/BondExplorer';
import { MarketRisk } from './pages/MarketRisk';
import { StressTesting } from './pages/StressTesting';
import { LiquidityRisk } from './pages/LiquidityRisk';
import { RiskControl } from './pages/RiskControl';
import { RiskLimits } from './pages/RiskLimits';
import { YieldCurve } from './pages/YieldCurve';
import { CreditRisk } from './pages/CreditRisk';
import { RiskIntelligence } from './pages/RiskIntelligence';
import { Reporting } from './pages/Reporting';
import { DataOperations } from './pages/DataOperations';
import { DataQuality } from './pages/DataQuality';
import { AnalyticsRuns } from './pages/AnalyticsRuns';
import { ScenarioLab } from './pages/ScenarioLab';
import { AdvancedRisk } from './pages/AdvancedRisk';
import { Login } from './pages/Login';
import { AuthProvider } from './auth/AuthProvider';
import { ProtectedRoute } from './auth/ProtectedRoute';
import * as perms from './auth/permissions';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout />}>
              <Route index element={
                <ProtectedRoute requiredPermission={perms.PORTFOLIO_READ}>
                  <Overview />
                </ProtectedRoute>
              } />
              <Route path="portfolio" element={
                <ProtectedRoute requiredPermission={perms.PORTFOLIO_READ}>
                  <Portfolio />
                </ProtectedRoute>
              } />
              <Route path="bond-explorer" element={
                <ProtectedRoute requiredPermission={perms.PORTFOLIO_READ}>
                  <BondExplorer />
                </ProtectedRoute>
              } />
              <Route path="market-risk" element={
                <ProtectedRoute requiredPermission={perms.RISK_READ}>
                  <MarketRisk />
                </ProtectedRoute>
              } />
              <Route path="credit-risk" element={
                <ProtectedRoute requiredPermission={perms.RISK_READ}>
                  <CreditRisk />
                </ProtectedRoute>
              } />
              <Route path="yield-curve" element={
                <ProtectedRoute requiredPermission={perms.PORTFOLIO_READ}>
                  <YieldCurve />
                </ProtectedRoute>
              } />
              <Route path="stress-testing" element={
                <ProtectedRoute requiredPermission={perms.RISK_READ}>
                  <StressTesting />
                </ProtectedRoute>
              } />
              <Route path="scenario-lab" element={
                <ProtectedRoute requiredPermission={perms.STRESS_EXECUTE}>
                  <ScenarioLab />
                </ProtectedRoute>
              } />
              <Route path="advanced-risk" element={
                <ProtectedRoute requiredPermission={perms.RISK_READ}>
                  <AdvancedRisk />
                </ProtectedRoute>
              } />
              <Route path="risk-intelligence" element={
                <ProtectedRoute requiredPermission={perms.RISK_READ}>
                  <RiskIntelligence />
                </ProtectedRoute>
              } />
              <Route path="liquidity-risk" element={
                <ProtectedRoute requiredPermission={perms.RISK_READ}>
                  <LiquidityRisk />
                </ProtectedRoute>
              } />
              <Route path="risk-control">
                <Route index element={
                  <ProtectedRoute requiredPermission={perms.RISK_READ}>
                    <RiskControl />
                  </ProtectedRoute>
                } />
                <Route path="limits" element={
                  <ProtectedRoute requiredPermission={perms.RISK_READ}>
                    <RiskLimits />
                  </ProtectedRoute>
                } />
              </Route>
              <Route path="reporting" element={
                <ProtectedRoute requiredPermission={perms.PORTFOLIO_READ}>
                  <Reporting />
                </ProtectedRoute>
              } />
              <Route path="data-monitor" element={
                <ProtectedRoute requiredPermission={perms.AUDIT_READ}>
                  <DataMonitor />
                </ProtectedRoute>
              } />
              <Route path="data-operations" element={
                <ProtectedRoute requiredPermission={perms.AUDIT_READ}>
                  <DataOperations />
                </ProtectedRoute>
              } />
              <Route path="data-quality" element={
                <ProtectedRoute requiredPermission={perms.AUDIT_READ}>
                  <DataQuality />
                </ProtectedRoute>
              } />
              <Route path="analytics-runs" element={
                <ProtectedRoute requiredPermission={perms.RISK_READ}>
                  <AnalyticsRuns />
                </ProtectedRoute>
              } />
              <Route path="system" element={
                <ProtectedRoute requiredPermission={perms.PORTFOLIO_READ}>
                  <System />
                </ProtectedRoute>
              } />
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;

