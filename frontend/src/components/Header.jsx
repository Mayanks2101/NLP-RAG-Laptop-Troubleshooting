import { useEffect, useState } from 'react';
import ThemeToggle from './ThemeToggle';
import { BrandLogo } from './BrandLogo';
import useChatStore from '../store/chatStore';
import { checkHealth } from '../api/client';

export default function Header() {
  const toggleDebugPanel = useChatStore((s) => s.toggleDebugPanel);
  const debugPanelOpen = useChatStore((s) => s.debugPanelOpen);
  const toggleSidebar = useChatStore((s) => s.toggleSidebar);
  const [healthOk, setHealthOk] = useState(null);

  useEffect(() => {
    checkHealth()
      .then((d) => setHealthOk(d.status === 'healthy'))
      .catch(() => setHealthOk(false));

    const iv = setInterval(() => {
      checkHealth()
        .then((d) => setHealthOk(d.status === 'healthy'))
        .catch(() => setHealthOk(false));
    }, 30_000);
    return () => clearInterval(iv);
  }, []);

  return (
    <header
      id="app-header"
      style={{
        height: 'var(--header-height)',
        background: 'var(--bg-secondary)',
        borderBottom: 'var(--glass-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        flexShrink: 0,
        zIndex: 20,
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
      }}
    >
      {/* Left: hamburger + title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Hamburger for mobile sidebar toggle */}
        <button
          id="sidebar-toggle-btn"
          onClick={toggleSidebar}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: 4,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1
              style={{
                fontSize: '1.25rem',
                fontWeight: 800,
                color: 'var(--logo-color)',
                lineHeight: 1,
                letterSpacing: '-0.02em',
                textShadow: 'var(--logo-glow)',
              }}
            >
              LaptopAI
            </h1>
            <span
              style={{
                fontSize: '0.65rem',
                color: 'var(--gold, var(--text-tertiary))',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginTop: '-2px',
              }}
            >
              RAG Troubleshooter
            </span>
          </div>
        </div>
      </div>

      {/* Right: health + debug + theme */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {/* Health indicator */}
        {healthOk !== null && (
          <div
            title={healthOk ? 'Backend connected' : 'Backend unavailable'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              background: healthOk ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
              border: `1px solid ${healthOk ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
              fontSize: '0.7rem',
              fontWeight: 500,
              color: healthOk ? 'var(--success)' : 'var(--error)',
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: healthOk ? 'var(--success)' : 'var(--error)',
                display: 'inline-block',
                animation: healthOk ? 'glow-pulse 2s infinite' : 'none',
              }}
            />
            {healthOk ? 'Connected' : 'Offline'}
          </div>
        )}

        {/* Debug panel toggle */}
        <button
          id="debug-toggle-btn"
          onClick={toggleDebugPanel}
          title="Toggle Debug Panel"
          style={{
            background: debugPanelOpen ? 'var(--accent-muted)' : 'var(--bg-hover)',
            border: `1px solid ${debugPanelOpen ? 'var(--accent)' : 'var(--border)'}`,
            borderRadius: 'var(--radius-sm)',
            padding: '6px 12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            color: debugPanelOpen ? 'var(--accent)' : 'var(--text-secondary)',
            fontSize: '0.78rem',
            fontWeight: 500,
            transition: 'all var(--transition-fast)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent)';
            e.currentTarget.style.color = 'var(--accent)';
          }}
          onMouseLeave={(e) => {
            if (!debugPanelOpen) {
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
          Debug
        </button>

        <ThemeToggle />
      </div>
    </header>
  );
}
