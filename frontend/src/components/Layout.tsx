import { Outlet, Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell } from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';
import { usePortfolio } from '../auth/PortfolioContext';
import * as perms from '../auth/permissions';
import {
  getNotifications,
  getUnreadNotificationsCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '../api/client';

const NAV_GROUPS = [
  {
    title: 'Dashboard',
    items: [{ path: '/', label: 'Overview', permission: perms.PORTFOLIO_READ }],
  },
  {
    title: 'Portfolio',
    items: [
      { path: '/portfolio',     label: 'Portfolio',     permission: perms.PORTFOLIO_READ },
      { path: '/bond-explorer', label: 'Bond Explorer', permission: perms.PORTFOLIO_READ },
    ],
  },
  {
    title: 'Risk Analytics',
    items: [
      { path: '/yield-curve',      label: 'Yield Curve',      permission: perms.PORTFOLIO_READ },
      { path: '/credit-risk',      label: 'Credit Risk',      permission: perms.RISK_READ },
      { path: '/market-risk',      label: 'Market Risk',      permission: perms.RISK_READ },
      { path: '/stress-testing',   label: 'Stress Testing',   permission: perms.RISK_READ },
      { path: '/scenario-lab',     label: 'Scenario Lab',     permission: perms.STRESS_EXECUTE },
      { path: '/advanced-risk',    label: 'Advanced Analytics', permission: perms.RISK_READ },
      { path: '/liquidity-risk',   label: 'Liquidity Risk',   permission: perms.RISK_READ },
      { path: '/risk-intelligence',label: 'Risk Intelligence', permission: perms.RISK_READ },
    ],
  },
  {
    title: 'Governance',
    items: [
      { path: '/risk-control',       label: 'Risk Control',       permission: perms.RISK_READ },
      { path: '/risk-control/limits',label: 'Risk Limits',        permission: perms.RISK_READ },
      { path: '/reporting',          label: 'Executive Reporting', permission: perms.PORTFOLIO_READ },
    ],
  },
  {
    title: 'Operations',
    items: [
      { path: '/data-monitor',    label: 'Data Monitor',    permission: perms.AUDIT_READ },
      { path: '/data-operations', label: 'Data Operations', permission: perms.AUDIT_READ },
      { path: '/data-quality',    label: 'Data Quality',    permission: perms.AUDIT_READ },
      { path: '/analytics-runs',  label: 'Analytics Runs',  permission: perms.RISK_READ },
      { path: '/system',          label: 'System',          permission: perms.PORTFOLIO_READ },
    ],
  },
];

// ─── Layout ────────────────────────────────────────────────────────
export const Layout = () => {
  const location = useLocation();
  const { user, logout, hasPermission } = useAuth();
  const { selectedPortfolioId, portfolios, selectPortfolio } = usePortfolio();
  const queryClient = useQueryClient();
  const [notifOpen, setNotifOpen] = useState(false);
  const today = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });

  const { data: notifCountData } = useQuery({
    queryKey: ['unreadNotificationsCount'],
    queryFn: getUnreadNotificationsCount,
    refetchInterval: 15000,
  });

  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
    enabled: notifOpen,
  });

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreadNotificationsCount'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreadNotificationsCount'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const unreadCount = notifCountData?.unread_count ?? 0;

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', backgroundColor: 'var(--bg-root)' }}>

      {/* ── Left nav rail ── */}
      <aside style={{
        width: '224px',
        minWidth: '224px',
        backgroundColor: 'var(--bg-shell)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        flexShrink: 0,
      }}>

        {/* Wordmark */}
        <div style={{ padding: '20px 20px 18px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            BondGuard<span style={{ color: 'var(--accent)' }}> Pro</span>
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px', letterSpacing: '0.04em' }}>
            Fixed Income Risk Platform
          </div>
        </div>

        {/* Nav groups */}
        <nav style={{ flex: 1, padding: '14px 0' }}>
          {NAV_GROUPS.map((group) => {
            const visible = group.items.filter(i => hasPermission(i.permission));
            if (visible.length === 0) return null;
            return (
              <div key={group.title} style={{ marginBottom: '4px' }}>
                <div style={{
                  fontSize: '9px', fontWeight: 700, letterSpacing: '0.12em',
                  textTransform: 'uppercase', color: 'var(--text-muted)',
                  padding: '10px 20px 4px',
                }}>
                  {group.title}
                </div>
                {visible.map((item) => {
                  const active = location.pathname === item.path ||
                    (item.path !== '/' && location.pathname.startsWith(item.path));
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      style={{
                        display: 'block',
                        padding: '7px 20px 7px 17px',
                        fontSize: '12.5px',
                        fontWeight: active ? 500 : 400,
                        color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                        backgroundColor: active ? 'var(--bg-panel-hover)' : 'transparent',
                        borderLeft: active ? '3px solid var(--accent)' : '3px solid transparent',
                        textDecoration: 'none',
                        transition: 'var(--transition)',
                        letterSpacing: '0.01em',
                      }}
                      onMouseEnter={e => { if (!active) { e.currentTarget.style.backgroundColor = 'var(--bg-panel)'; e.currentTarget.style.color = 'var(--text-primary)'; }}}
                      onMouseLeave={e => { if (!active) { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            );
          })}
          {hasPermission(perms.USER_MANAGE) && (
            <div style={{ marginBottom: '4px' }}>
              <div style={{
                fontSize: '9px', fontWeight: 700, letterSpacing: '0.12em',
                textTransform: 'uppercase', color: 'var(--text-muted)',
                padding: '10px 20px 4px',
              }}>
                Admin Portal
              </div>
              {[
                { path: '/admin/portfolios', label: 'Portfolios' },
                { path: '/admin/bonds',      label: 'Bonds Master' },
                { path: '/admin/transactions', label: 'Transactions' },
              ].map((item) => {
                const active = location.pathname.startsWith(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    style={{
                      display: 'block',
                      padding: '7px 20px 7px 17px',
                      fontSize: '12.5px',
                      fontWeight: active ? 500 : 400,
                      color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
                      backgroundColor: active ? 'var(--bg-panel-hover)' : 'transparent',
                      borderLeft: active ? '3px solid var(--accent)' : '3px solid transparent',
                      textDecoration: 'none',
                      transition: 'var(--transition)',
                      letterSpacing: '0.01em',
                    }}
                    onMouseEnter={e => { if (!active) { e.currentTarget.style.backgroundColor = 'var(--bg-panel)'; e.currentTarget.style.color = 'var(--text-primary)'; }}}
                    onMouseLeave={e => { if (!active) { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          )}
        </nav>

        {/* User block */}
        {user && (
          <div style={{ padding: '14px 20px', borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '1px' }}>
              {user.username}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '10px' }}>
              {user.roles.join(', ')}
            </div>
            <button
              onClick={() => logout()}
              style={{
                width: '100%', padding: '6px 12px', backgroundColor: 'transparent',
                border: '1px solid var(--border-muted)', borderRadius: 'var(--radius-sm)',
                color: 'var(--text-muted)', fontSize: '11px', cursor: 'pointer',
                fontFamily: 'var(--font-sans)', transition: 'var(--transition)',
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-danger)'; e.currentTarget.style.color = 'var(--text-critical)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-muted)'; e.currentTarget.style.color = 'var(--text-muted)'; }}
            >
              Sign Out
            </button>
          </div>
        )}
      </aside>

      {/* ── Main column ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Top bar */}
        <header style={{
          height: '52px', backgroundColor: 'var(--bg-shell)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px', flexShrink: 0,
        }}>
          {/* Context chips */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.10em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Portfolio</span>
              {portfolios && portfolios.length > 0 ? (
                <select
                  value={selectedPortfolioId || ''}
                  onChange={(e) => selectPortfolio(Number(e.target.value))}
                  style={{
                    backgroundColor: 'var(--bg-inset)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-muted)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11px',
                    fontWeight: 500,
                    padding: '3px 8px',
                    outline: 'none',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  {portfolios.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} {p.status === 'ARCHIVED' ? '(Archived)' : ''}
                    </option>
                  ))}
                </select>
              ) : (
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 500 }}>None</span>
              )}
            </div>
            <div style={{ width: '1px', height: '14px', backgroundColor: 'var(--border-subtle)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.10em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Valuation</span>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>{today}</span>
            </div>
          </div>

          {/* Right side */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* Notification bell */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setNotifOpen(o => !o)}
                style={{
                  background: 'transparent', border: 'none', cursor: 'pointer',
                  color: 'var(--text-muted)', display: 'flex', alignItems: 'center',
                  padding: '4px', position: 'relative',
                }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
              >
                <Bell size={16} />
                {unreadCount > 0 && (
                  <span style={{
                    position: 'absolute', top: '-2px', right: '-2px',
                    backgroundColor: 'var(--text-critical)', color: '#fff',
                    fontSize: '9px', fontWeight: 700, borderRadius: '9999px',
                    padding: '0 4px', lineHeight: '14px', minWidth: '14px', textAlign: 'center',
                  }}>
                    {unreadCount}
                  </span>
                )}
              </button>

              {notifOpen && (
                <>
                  <div onClick={() => setNotifOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 99 }} />
                  <div style={{
                    position: 'absolute', right: 0, top: '32px', width: '300px',
                    backgroundColor: 'var(--bg-panel)',
                    border: '1px solid var(--border-muted)',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: '0 16px 32px rgba(0,0,0,0.5)',
                    zIndex: 100, overflow: 'hidden',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderBottom: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-inset)' }}>
                      <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Notifications</span>
                      {unreadCount > 0 && (
                        <button onClick={() => markAllReadMutation.mutate()} style={{ background: 'none', border: 'none', color: 'var(--text-accent)', fontSize: '10px', cursor: 'pointer' }}>
                          Mark all read
                        </button>
                      )}
                    </div>
                    <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
                      {notifications && notifications.length > 0 ? notifications.map((n: any) => (
                        <div
                          key={n.id}
                          onClick={() => !n.is_read && markReadMutation.mutate(n.id)}
                          style={{
                            padding: '10px 14px', borderBottom: '1px solid var(--border-subtle)',
                            cursor: n.is_read ? 'default' : 'pointer',
                            backgroundColor: n.is_read ? 'transparent' : 'rgba(16,185,129,0.04)',
                          }}
                        >
                          <div style={{ fontSize: '12px', fontWeight: n.is_read ? 400 : 600, color: 'var(--text-primary)' }}>{n.title}</div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{n.message}</div>
                        </div>
                      )) : (
                        <div style={{ padding: '24px', textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>No notifications</div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '28px 32px', backgroundColor: 'var(--bg-root)' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
