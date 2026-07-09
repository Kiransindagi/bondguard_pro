import { Outlet, Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell } from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';
import * as perms from '../auth/permissions';
import { getNotifications, getUnreadNotificationsCount, markNotificationRead, markAllNotificationsRead } from '../api/client';

const navGroups = [
  {
    title: 'Dashboard',
    items: [{ path: '/', label: 'Overview', permission: perms.PORTFOLIO_READ }]
  },
  {
    title: 'Portfolio',
    items: [
      { path: '/portfolio', label: 'Portfolio', permission: perms.PORTFOLIO_READ },
      { path: '/bond-explorer', label: 'Bond Explorer', permission: perms.PORTFOLIO_READ }
    ]
  },
  {
    title: 'Risk Analytics',
    items: [
      { path: '/yield-curve', label: 'Yield Curve', permission: perms.PORTFOLIO_READ },
      { path: '/credit-risk', label: 'Credit Risk', permission: perms.RISK_READ },
      { path: '/market-risk', label: 'Market Risk', permission: perms.RISK_READ },
      { path: '/stress-testing', label: 'Stress Testing', permission: perms.RISK_READ },
      { path: '/scenario-lab', label: 'Scenario Lab', permission: perms.STRESS_EXECUTE },
      { path: '/advanced-risk', label: 'Advanced Analytics', permission: perms.RISK_READ },
      { path: '/liquidity-risk', label: 'Liquidity Risk', permission: perms.RISK_READ },
      { path: '/risk-intelligence', label: 'Risk Intelligence', permission: perms.RISK_READ }
    ]
  },
  {
    title: 'Governance',
    items: [
      { path: '/risk-control', label: 'Risk Control', permission: perms.RISK_READ },
      { path: '/risk-control/limits', label: 'Risk Limits', permission: perms.RISK_READ },
      { path: '/reporting', label: 'Executive Reporting', permission: perms.PORTFOLIO_READ }
    ]
  },
  {
    title: 'Operations',
    items: [
      { path: '/data-monitor', label: 'Data Monitor', permission: perms.AUDIT_READ },
      { path: '/data-operations', label: 'Data Operations', permission: perms.AUDIT_READ },
      { path: '/data-quality', label: 'Data Quality', permission: perms.AUDIT_READ },
      { path: '/analytics-runs', label: 'Analytics Runs', permission: perms.RISK_READ },
      { path: '/system', label: 'System', permission: perms.PORTFOLIO_READ }
    ]
  }
];

export const Layout = () => {
  const location = useLocation();
  const { user, logout, hasPermission } = useAuth();
  const queryClient = useQueryClient();
  const [notifOpen, setNotifOpen] = useState(false);

  const { data: notifCountData } = useQuery({
    queryKey: ['unreadNotificationsCount'],
    queryFn: getUnreadNotificationsCount,
    refetchInterval: 15000
  });

  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
    enabled: notifOpen
  });

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreadNotificationsCount'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreadNotificationsCount'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }
  });

  const unreadCount = notifCountData?.unread_count || 0;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0f172a', color: '#f1f5f9' }}>
      <aside style={{ width: '250px', backgroundColor: '#1e293b', padding: '1rem', borderRight: '1px solid #334155', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        <h2 style={{ color: '#38bdf8', marginBottom: '2rem' }}>BondGuard Pro</h2>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {navGroups.map((group) => {
            // Filter group items based on permission
            const visibleItems = group.items.filter(item => hasPermission(item.permission));
            if (visibleItems.length === 0) return null;

            return (
              <div key={group.title}>
                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  {group.title}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {visibleItems.map((item) => {
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
                      >
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>
      </aside>
      
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <header style={{ 
          height: '60px', 
          backgroundColor: '#1e293b', 
          borderBottom: '1px solid #334155', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          padding: '0 2rem' 
        }}>
          <div>
            {/* Left side empty or page title */}
          </div>
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              
              {/* Notification Bell */}
              <div style={{ position: 'relative' }}>
                <button 
                  onClick={() => setNotifOpen(!notifOpen)}
                  style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: '#cbd5e1',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0.25rem',
                    position: 'relative'
                  }}
                >
                  <Bell size={20} />
                  {unreadCount > 0 && (
                    <span style={{
                      position: 'absolute',
                      top: '-4px',
                      right: '-4px',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      fontSize: '0.625rem',
                      fontWeight: 'bold',
                      borderRadius: '9999px',
                      padding: '0.1rem 0.35rem'
                    }}>
                      {unreadCount}
                    </span>
                  )}
                </button>

                {/* Dropdown Overlay */}
                {notifOpen && (
                  <div style={{
                    position: 'absolute',
                    right: 0,
                    top: '35px',
                    width: '320px',
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)',
                    zIndex: 1000,
                    overflow: 'hidden'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', borderBottom: '1px solid #334155', backgroundColor: '#0f172a' }}>
                      <span style={{ fontWeight: 'bold', fontSize: '0.875rem' }}>Notifications</span>
                      {unreadCount > 0 && (
                        <button 
                          onClick={() => markAllReadMutation.mutate()}
                          style={{ backgroundColor: 'transparent', border: 'none', color: '#38bdf8', fontSize: '0.75rem', cursor: 'pointer' }}
                        >
                          Mark all read
                        </button>
                      )}
                    </div>
                    <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                      {notifications && notifications.length > 0 ? (
                        notifications.map((n: any) => (
                          <div 
                            key={n.id} 
                            onClick={() => !n.is_read && markReadMutation.mutate(n.id)}
                            style={{
                              padding: '0.75rem 1rem',
                              borderBottom: '1px solid #334155',
                              cursor: n.is_read ? 'default' : 'pointer',
                              backgroundColor: n.is_read ? 'transparent' : '#1e3a8a33',
                              fontSize: '0.8125rem'
                            }}
                          >
                            <div style={{ fontWeight: n.is_read ? 'normal' : 'bold', color: '#f1f5f9' }}>{n.title}</div>
                            <div style={{ color: '#94a3b8', marginTop: '0.25rem', fontSize: '0.75rem' }}>{n.message}</div>
                          </div>
                        ))
                      ) : (
                        <div style={{ padding: '1rem', color: '#64748b', textAlign: 'center', fontSize: '0.8125rem' }}>
                          No notifications.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 'semibold', color: '#f1f5f9' }}>{user.username}</span>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{user.roles.join(', ')}</span>
              </div>
              <button 
                onClick={() => logout()}
                style={{
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  padding: '0.4rem 1rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'semibold',
                  fontSize: '0.875rem',
                  transition: 'background-color 0.15s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
              >
                Sign Out
              </button>
            </div>
          )}
        </header>

        <main style={{ flex: 1, padding: '2rem', overflowY: 'auto', backgroundColor: '#0f172a' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

