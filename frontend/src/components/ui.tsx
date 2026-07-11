import React from 'react';

// ─── Design token shortcuts ────────────────────────────────────────
const T = {
  panel:       { backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' },
  panelInset:  { backgroundColor: 'var(--bg-inset)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' },
  textPrimary: { color: 'var(--text-primary)' },
  textSecond:  { color: 'var(--text-secondary)' },
  textMuted:   { color: 'var(--text-muted)' },
  label:       { fontSize: '10px', fontWeight: 600, letterSpacing: '0.10em', textTransform: 'uppercase' as const, color: 'var(--text-muted)' },
  sectionHead: { fontSize: '11px', fontWeight: 600, letterSpacing: '0.09em', textTransform: 'uppercase' as const, color: 'var(--text-muted)' },
  mono:        { fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums' },
};

// ─── PageHeader ────────────────────────────────────────────────────
interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: { label: string; variant: 'ok' | 'warning' | 'danger' | 'info' | 'muted' };
  action?: React.ReactNode;
  context?: string; // e.g. "Valuation: 06 Jul 2026"
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, description, badge, action, context }) => (
  <div style={{ marginBottom: '28px', paddingBottom: '20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: description ? '4px' : 0 }}>
        <h1 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>{title}</h1>
        {badge && <StatusBadge label={badge.label} variant={badge.variant} />}
      </div>
      {description && <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{description}</p>}
      {context && <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', fontVariantNumeric: 'tabular-nums' }}>{context}</p>}
    </div>
    {action && <div style={{ flexShrink: 0 }}>{action}</div>}
  </div>
);

// ─── SectionHeader ─────────────────────────────────────────────────
interface SectionHeaderProps {
  title: string;
  action?: React.ReactNode;
  style?: React.CSSProperties;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ title, action, style }) => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', ...style }}>
    <span style={T.sectionHead}>{title}</span>
    {action && <div>{action}</div>}
  </div>
);

// ─── StatusBadge ───────────────────────────────────────────────────
const BADGE_STYLES = {
  ok:      { color: 'var(--text-positive)', backgroundColor: 'rgba(52,211,153,0.10)', border: '1px solid rgba(52,211,153,0.25)' },
  warning: { color: 'var(--text-warning)',  backgroundColor: 'rgba(251,191,36,0.10)',  border: '1px solid rgba(251,191,36,0.28)' },
  danger:  { color: 'var(--text-critical)', backgroundColor: 'rgba(248,113,113,0.10)', border: '1px solid rgba(248,113,113,0.28)' },
  info:    { color: 'var(--text-info)',     backgroundColor: 'rgba(103,232,249,0.08)', border: '1px solid rgba(103,232,249,0.25)' },
  muted:   { color: 'var(--text-muted)',    backgroundColor: 'rgba(148,163,184,0.08)', border: '1px solid rgba(148,163,184,0.18)' },
};

interface StatusBadgeProps {
  label: string;
  variant: keyof typeof BADGE_STYLES;
  style?: React.CSSProperties;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ label, variant, style }) => (
  <span style={{
    ...BADGE_STYLES[variant],
    fontSize: '10px',
    fontWeight: 600,
    letterSpacing: '0.07em',
    padding: '2px 8px',
    borderRadius: '3px',
    textTransform: 'uppercase',
    whiteSpace: 'nowrap',
    ...style,
  }}>
    {label}
  </span>
);

// ─── MetricCard ────────────────────────────────────────────────────
interface MetricCardProps {
  label: string;
  value: string | number | React.ReactNode;
  unit?: string;
  sub?: string | React.ReactNode;
  accent?: boolean;
  warning?: boolean;
  danger?: boolean;
  style?: React.CSSProperties;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, unit, sub, accent, warning, danger, style }) => {
  const border = danger ? 'var(--border-danger)' : warning ? 'var(--border-warning)' : accent ? 'var(--border-emphasis)' : 'var(--border-subtle)';
  const glow = danger ? 'rgba(248,113,113,0.04)' : warning ? 'rgba(251,191,36,0.04)' : accent ? 'var(--accent-dim)' : 'transparent';
  return (
    <div style={{
      backgroundColor: 'var(--bg-panel)',
      border: `1px solid ${border}`,
      borderRadius: 'var(--radius-md)',
      padding: '18px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '6px',
      boxShadow: `0 0 0 1px ${glow} inset`,
      ...style,
    }}>
      <div style={T.label}>{label}</div>
      <div style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums', lineHeight: 1.1, letterSpacing: '-0.01em' }}>
        {value}
        {unit && <span style={{ fontSize: '14px', fontWeight: 400, color: 'var(--text-muted)', marginLeft: '4px' }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>{sub}</div>}
    </div>
  );
};

// ─── DataPanel ─────────────────────────────────────────────────────
interface DataPanelProps {
  title?: string;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  style?: React.CSSProperties;
  bodyStyle?: React.CSSProperties;
  noPad?: boolean;
}

export const DataPanel: React.FC<DataPanelProps> = ({ title, headerAction, children, style, bodyStyle, noPad }) => (
  <div style={{ ...T.panel, overflow: 'hidden', ...style }}>
    {title && (
      <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={T.sectionHead}>{title}</span>
        {headerAction}
      </div>
    )}
    <div style={{ padding: noPad ? 0 : '18px 20px', ...bodyStyle }}>
      {children}
    </div>
  </div>
);

// ─── ModelStatusBanner ─────────────────────────────────────────────
interface ModelStatusBannerProps {
  status: string;
  message?: string;
  variant?: 'warning' | 'info' | 'danger';
}

export const ModelStatusBanner: React.FC<ModelStatusBannerProps> = ({ status, message, variant = 'warning' }) => {
  const styles = {
    warning: { bg: 'rgba(251,191,36,0.07)', border: 'var(--border-warning)', color: 'var(--text-warning)' },
    info:    { bg: 'rgba(103,232,249,0.06)', border: 'var(--border-info)',    color: 'var(--text-info)' },
    danger:  { bg: 'rgba(248,113,113,0.07)', border: 'var(--border-danger)', color: 'var(--text-critical)' },
  }[variant];

  return (
    <div style={{
      backgroundColor: styles.bg,
      border: `1px solid ${styles.border}`,
      borderRadius: 'var(--radius-md)',
      padding: '10px 16px',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      marginBottom: '20px',
    }}>
      <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: styles.color, flexShrink: 0, marginTop: '4px' }} />
      <div>
        <span style={{ color: styles.color, fontWeight: 600, fontSize: '11px', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{status}</span>
        {message && <p style={{ color: styles.color, fontSize: '11px', marginTop: '2px', opacity: 0.8 }}>{message}</p>}
      </div>
    </div>
  );
};

// ─── EmptyState ────────────────────────────────────────────────────
interface EmptyStateProps { message?: string; }
export const EmptyState: React.FC<EmptyStateProps> = ({ message = 'No data available.' }) => (
  <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
    {message}
  </div>
);

// ─── LoadingState ──────────────────────────────────────────────────
interface LoadingStateProps { message?: string; }
export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Loading...' }) => (
  <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
    {message}
  </div>
);

// ─── ErrorState ────────────────────────────────────────────────────
interface ErrorStateProps { message?: string; }
export const ErrorState: React.FC<ErrorStateProps> = ({ message = 'Failed to load data.' }) => (
  <div style={{ padding: '32px 24px', textAlign: 'center', color: 'var(--text-critical)', fontSize: '13px' }}>
    {message}
  </div>
);

// ─── Table primitives ──────────────────────────────────────────────
export const TablePanel: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ overflowX: 'auto', ...style }}>
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', color: 'var(--text-primary)' }}>
      {children}
    </table>
  </div>
);

export const Th: React.FC<{ children: React.ReactNode; right?: boolean; style?: React.CSSProperties }> = ({ children, right, style }) => (
  <th style={{
    padding: '8px 14px',
    textAlign: right ? 'right' : 'left',
    fontWeight: 600,
    fontSize: '10px',
    letterSpacing: '0.09em',
    textTransform: 'uppercase',
    color: 'var(--text-muted)',
    borderBottom: '1px solid var(--border-muted)',
    whiteSpace: 'nowrap',
    ...style,
  }}>{children}</th>
);

export const Td: React.FC<{ children: React.ReactNode; right?: boolean; mono?: boolean; style?: React.CSSProperties }> = ({ children, right, mono, style }) => (
  <td style={{
    padding: '9px 14px',
    textAlign: right ? 'right' : 'left',
    borderBottom: '1px solid var(--border-subtle)',
    color: 'var(--text-primary)',
    fontVariantNumeric: mono ? 'tabular-nums' : undefined,
    whiteSpace: 'nowrap',
    ...style,
  }}>{children}</td>
);

// ─── PrimaryButton ─────────────────────────────────────────────────
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md';
}

const BTN_BASE: React.CSSProperties = {
  display: 'inline-flex', alignItems: 'center', gap: '6px',
  border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)',
  fontWeight: 500, borderRadius: 'var(--radius-sm)', transition: 'var(--transition)',
  letterSpacing: '0.01em',
};

const BTN_VARIANTS = {
  primary:   { backgroundColor: 'var(--accent)',        color: '#fff',                  border: 'none' },
  secondary: { backgroundColor: 'var(--bg-elevated)',    color: 'var(--text-primary)',    border: '1px solid var(--border-muted)' },
  ghost:     { backgroundColor: 'transparent',          color: 'var(--text-secondary)',  border: '1px solid var(--border-subtle)' },
  danger:    { backgroundColor: 'rgba(248,113,113,0.12)', color: 'var(--text-critical)', border: '1px solid var(--border-danger)' },
};

const BTN_SIZES = {
  sm: { fontSize: '11px', padding: '5px 12px' },
  md: { fontSize: '12px', padding: '7px 16px' },
};

export const Btn: React.FC<ButtonProps> = ({ children, variant = 'secondary', size = 'md', style, ...rest }) => (
  <button style={{ ...BTN_BASE, ...BTN_VARIANTS[variant], ...BTN_SIZES[size], ...style }} {...rest}>
    {children}
  </button>
);

// ─── Divider ───────────────────────────────────────────────────────
export const Divider: React.FC<{ style?: React.CSSProperties }> = ({ style }) => (
  <div style={{ height: '1px', backgroundColor: 'var(--border-subtle)', margin: '20px 0', ...style }} />
);

// ─── KV row (key-value pair) ────────────────────────────────────────
export const KVRow: React.FC<{ label: string; value: React.ReactNode; style?: React.CSSProperties }> = ({ label, value, style }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', ...style }}>
    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{label}</span>
    <span style={{ fontSize: '12px', color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
  </div>
);
