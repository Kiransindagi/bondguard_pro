import { Outlet, Link, useLocation } from 'react-router-dom';

const navGroups = [
  {
    title: 'Dashboard',
    items: [{ path: '/', label: 'Overview' }]
  },
  {
    title: 'Portfolio',
    items: [
      { path: '/portfolio', label: 'Portfolio' },
      { path: '/bond-explorer', label: 'Bond Explorer' }
    ]
  },
  {
    title: 'Risk Analytics',
    items: [
      { path: '/yield-curve', label: 'Yield Curve' },
      { path: '/credit-risk', label: 'Credit Risk' },
      { path: '/market-risk', label: 'Market Risk' },
      { path: '/stress-testing', label: 'Stress Testing' },
      { path: '/liquidity-risk', label: 'Liquidity Risk' },
      { path: '/risk-intelligence', label: 'Risk Intelligence' }
    ]
  },
  {
    title: 'Governance',
    items: [
      { path: '/risk-control', label: 'Risk Control' },
      { path: '/risk-control/limits', label: 'Risk Limits' },
      { path: '/reporting', label: 'Executive Reporting' }
    ]
  },
  {
    title: 'Operations',
    items: [
      { path: '/data-monitor', label: 'Data Monitor' },
      { path: '/system', label: 'System' }
    ]
  }
];

export const Layout = () => {
  const location = useLocation();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0f172a', color: '#f1f5f9' }}>
      <aside style={{ width: '250px', backgroundColor: '#1e293b', padding: '1rem', borderRight: '1px solid #334155', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        <h2 style={{ color: '#38bdf8', marginBottom: '2rem' }}>BondGuard Pro</h2>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {navGroups.map((group) => (
            <div key={group.title}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                {group.title}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {group.items.map((item) => {
                  const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path + '/'));
                  return (
                    <Link 
                      key={item.path} 
                      to={item.path}
                      style={{ 
                        textDecoration: 'none', 
                        color: isActive ? '#38bdf8' : '#cbd5e1', 
                        padding: '0.5rem', 
                        borderRadius: '4px',
                        backgroundColor: isActive ? '#334155' : 'transparent',
                        transition: 'background-color 0.2s, color 0.2s'
                      }}
                      onMouseOver={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = '#1e293b'; }}
                      onMouseOut={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>
      <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
        <Outlet />
      </main>
    </div>
  );
};
