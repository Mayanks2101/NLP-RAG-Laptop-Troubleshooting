/**
 * Royal brand logo — a stylized crown/shield AI icon.
 * Used in Header, ChatWindow hero, and message avatars.
 */

export function BrandLogo({ size = 32 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size > 40 ? 16 : 8,
        background: 'var(--brand-bg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 15px rgba(6, 182, 212, 0.4)',
        flexShrink: 0,
      }}
    >
      <svg
        width={size * 0.55}
        height={size * 0.55}
        viewBox="0 0 24 24"
        fill="none"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* Crown shape */}
        <path d="M2 18L5 8L9 13L12 4L15 13L19 8L22 18H2Z" fill="var(--brand-stroke)" style={{ opacity: 0.15 }} />
        <path d="M2 18L5 8L9 13L12 4L15 13L19 8L22 18H2Z" stroke="var(--brand-stroke)" />
        {/* Base line */}
        <line x1="3" y1="21" x2="21" y2="21" stroke="var(--brand-stroke)" strokeWidth="2" />
        {/* Gems */}
        <circle cx="12" cy="16" r="1" fill="var(--brand-stroke)" stroke="var(--brand-stroke)" strokeWidth="1" />
        <circle cx="8" cy="16" r="0.7" fill="var(--brand-stroke)" stroke="var(--brand-stroke)" strokeWidth="0.8" />
        <circle cx="16" cy="16" r="0.7" fill="var(--brand-stroke)" stroke="var(--brand-stroke)" strokeWidth="0.8" />
      </svg>
    </div>
  );
}

export function AssistantAvatar({ size = 32 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: 8,
        background: 'linear-gradient(135deg, #06b6d4, #00ffcc)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 10px rgba(6, 182, 212, 0.3)',
        flexShrink: 0,
      }}
    >
      <svg
        width={size * 0.5}
        height={size * 0.5}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#fff"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* AI brain/sparkle */}
        <path d="M12 2L14 8L20 8L15 12L17 18L12 14L7 18L9 12L4 8L10 8Z" fill="rgba(255,255,255,0.4)" />
        <path d="M12 2L14 8L20 8L15 12L17 18L12 14L7 18L9 12L4 8L10 8Z" />
      </svg>
    </div>
  );
}

export function UserAvatar({ size = 32 }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: 8,
        background: 'var(--bg-hover)',
        border: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      <svg
        width={size * 0.5}
        height={size * 0.5}
        viewBox="0 0 24 24"
        fill="none"
        stroke="var(--text-tertiary)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    </div>
  );
}
