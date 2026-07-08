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

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="portfolio" element={<Portfolio />} />
            <Route path="bond-explorer" element={<BondExplorer />} />
            <Route path="market-risk" element={<MarketRisk />} />
            <Route path="credit-risk" element={<CreditRisk />} />
            <Route path="yield-curve" element={<YieldCurve />} />
            <Route path="stress-testing" element={<StressTesting />} />
            <Route path="risk-intelligence" element={<RiskIntelligence />} />
            <Route path="liquidity-risk" element={<LiquidityRisk />} />
            <Route path="risk-control">
              <Route index element={<RiskControl />} />
              <Route path="limits" element={<RiskLimits />} />
            </Route>
            <Route path="reporting" element={<Reporting />} />
            <Route path="data-monitor" element={<DataMonitor />} />
            <Route path="system" element={<System />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
