import { useState, useRef, useEffect } from 'react';
import useChatStore from '../store/chatStore';

export default function InputBox({ onSend }) {
  const [value, setValue] = useState('');
  const isGenerating = useChatStore((s) => s.isGenerating);
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    const maxH = 160; // ~6 rows
    ta.style.height = Math.min(ta.scrollHeight, maxH) + 'px';
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      id="input-box"
      style={{
        padding: '12px 20px 16px',
        borderTop: 'var(--glass-border)',
        background: 'var(--bg-secondary)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 10,
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '8px 12px',
          transition: 'border-color var(--transition-fast), box-shadow var(--transition-fast)',
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = 'var(--accent)';
          e.currentTarget.style.boxShadow = '0 0 0 3px var(--accent-glow)';
        }}
        onBlur={(e) => {
          // Only remove focus style if focus leaves the container entirely
          if (!e.currentTarget.contains(e.relatedTarget)) {
            e.currentTarget.style.borderColor = 'var(--border)';
            e.currentTarget.style.boxShadow = 'none';
          }
        }}
      >
        <textarea
          ref={textareaRef}
          id="message-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isGenerating ? 'Waiting for response…' : 'Ask about laptop issues…'}
          disabled={isGenerating}
          rows={1}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: 'var(--text-primary)',
            fontSize: '0.9rem',
            fontFamily: 'var(--font-sans)',
            lineHeight: 1.5,
            resize: 'none',
            overflow: 'hidden',
            minHeight: 24,
          }}
        />

        <button
          id="send-btn"
          onClick={handleSend}
          disabled={!value.trim() || isGenerating}
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            background: value.trim() && !isGenerating ? 'var(--accent)' : 'var(--bg-hover)',
            color: value.trim() && !isGenerating ? '#fff' : 'var(--text-tertiary)',
            cursor: value.trim() && !isGenerating ? 'pointer' : 'not-allowed',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all var(--transition-fast)',
            flexShrink: 0,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>

      <div
        style={{
          textAlign: 'center',
          marginTop: 8,
          fontSize: '0.65rem',
          color: 'var(--text-tertiary)',
        }}
      >
        Press <kbd style={{ padding: '1px 5px', borderRadius: 3, border: '1px solid var(--border)', background: 'var(--bg-hover)', fontSize: '0.6rem' }}>Enter</kbd> to send · <kbd style={{ padding: '1px 5px', borderRadius: 3, border: '1px solid var(--border)', background: 'var(--bg-hover)', fontSize: '0.6rem' }}>Shift+Enter</kbd> for new line
      </div>
    </div>
  );
}
