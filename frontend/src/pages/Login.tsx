import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, error, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    const success = await login(username, password);
    if (success) {
      navigate(from, { replace: true });
    }
  };

  return (
    <div style={{
      minHeight: '100vh', width: '100vw',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      backgroundColor: 'var(--bg-root)',
      position: 'relative', overflow: 'hidden',
      fontFamily: 'var(--font-sans)',
    }}>
      {/* Ambient glow */}
      <div style={{
        position: 'absolute', top: '20%', left: '35%',
        width: '420px', height: '420px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '10%', right: '25%',
        width: '360px', height: '360px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(56,189,248,0.04) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Login panel */}
      <div style={{
        width: '100%', maxWidth: '380px',
        backgroundColor: 'var(--bg-panel)',
        border: '1px solid var(--border-muted)',
        borderRadius: 'var(--radius-lg)',
        padding: '40px 36px 36px',
        position: 'relative', zIndex: 1,
      }}>
        {/* Logo mark */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '42px', height: '42px', margin: '0 auto 18px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--accent-dim)',
            border: '1px solid var(--accent-border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            BondGuard<span style={{ color: 'var(--accent)' }}> Pro</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', letterSpacing: '0.04em' }}>
            Institutional Fixed Income Risk Platform
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{
              backgroundColor: 'rgba(248,113,113,0.08)',
              border: '1px solid var(--border-danger)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 14px', marginBottom: '20px',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}>
              <div style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: 'var(--text-critical)', flexShrink: 0 }} />
              <span style={{ fontSize: '12px', color: 'var(--text-critical)' }}>{error}</span>
            </div>
          )}

          <div style={{ marginBottom: '18px' }}>
            <label style={{
              display: 'block', fontSize: '10px', fontWeight: 600,
              letterSpacing: '0.10em', textTransform: 'uppercase',
              color: 'var(--text-muted)', marginBottom: '6px',
            }}>
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="analyst / manager / admin"
              style={{
                width: '100%', padding: '10px 14px',
                backgroundColor: 'var(--bg-inset)',
                border: '1px solid var(--border-muted)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)', fontSize: '13px',
                fontFamily: 'var(--font-sans)',
                outline: 'none', transition: 'var(--transition)',
              }}
              onFocus={e => e.currentTarget.style.borderColor = 'var(--accent-border)'}
              onBlur={e => e.currentTarget.style.borderColor = 'var(--border-muted)'}
            />
          </div>

          <div style={{ marginBottom: '26px' }}>
            <label style={{
              display: 'block', fontSize: '10px', fontWeight: 600,
              letterSpacing: '0.10em', textTransform: 'uppercase',
              color: 'var(--text-muted)', marginBottom: '6px',
            }}>
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter password"
              style={{
                width: '100%', padding: '10px 14px',
                backgroundColor: 'var(--bg-inset)',
                border: '1px solid var(--border-muted)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)', fontSize: '13px',
                fontFamily: 'var(--font-sans)',
                outline: 'none', transition: 'var(--transition)',
              }}
              onFocus={e => e.currentTarget.style.borderColor = 'var(--accent-border)'}
              onBlur={e => e.currentTarget.style.borderColor = 'var(--border-muted)'}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '10px',
              backgroundColor: 'var(--accent)',
              border: 'none', borderRadius: 'var(--radius-sm)',
              color: '#fff', fontSize: '13px', fontWeight: 600,
              fontFamily: 'var(--font-sans)',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              transition: 'var(--transition)',
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div style={{
          marginTop: '28px', paddingTop: '18px',
          borderTop: '1px solid var(--border-subtle)',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.03em' }}>
            Secure authentication with role-based access control
          </p>
        </div>
      </div>
    </div>
  );
};
