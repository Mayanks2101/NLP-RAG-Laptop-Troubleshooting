import { useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useMessageAnimation } from '../hooks/useGsapAnimations';
import { AssistantAvatar, UserAvatar } from './BrandLogo';

function formatTimestamp(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now - d;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ message }) {
  const ref = useRef(null);
  const isUser = message.role === 'user';

  useMessageAnimation(ref);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
  };

  return (
    <div
      ref={ref}
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        padding: '6px 0',
        opacity: 0, // GSAP will animate this
      }}
    >
      <div style={{ display: 'flex', gap: 10, maxWidth: '78%', alignItems: 'flex-start' }}>
        {/* Assistant avatar */}
        {!isUser && (
          <div style={{ marginTop: 2 }}>
            <AssistantAvatar size={32} />
          </div>
        )}

        <div style={{ minWidth: 0 }}>
          {/* Bubble */}
          <div
            style={{
              padding: isUser ? '10px 16px' : '14px 18px',
              borderRadius: isUser
                ? 'var(--radius-lg) var(--radius-lg) 4px var(--radius-lg)'
                : 'var(--radius-lg) var(--radius-lg) var(--radius-lg) 4px',
              background: isUser ? 'var(--bg-bubble-user)' : 'var(--bg-bubble-assistant)',
              color: isUser ? 'var(--text-bubble-user)' : 'var(--text-primary)',
              boxShadow: 'var(--shadow-bubble)',
              border: '1px solid var(--border-subtle)',
              backdropFilter: 'var(--glass-blur)',
              WebkitBackdropFilter: 'var(--glass-blur)',
              fontSize: isUser ? '0.9rem' : undefined,
              lineHeight: isUser ? 1.6 : undefined,
              wordBreak: 'break-word',
            }}
          >
            {isUser ? (
              <span>{message.content}</span>
            ) : (
              <div className="markdown-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      if (!inline && match) {
                        return (
                          <div style={{ position: 'relative' }}>
                            <div
                              style={{
                                position: 'absolute',
                                top: 6,
                                right: 8,
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                              }}
                            >
                              <span
                                style={{
                                  fontSize: '0.65rem',
                                  color: 'var(--text-tertiary)',
                                  textTransform: 'uppercase',
                                  fontWeight: 500,
                                }}
                              >
                                {match[1]}
                              </span>
                              <button
                                onClick={() => navigator.clipboard.writeText(String(children))}
                                style={{
                                  background: 'rgba(255,255,255,0.08)',
                                  border: '1px solid rgba(255,255,255,0.1)',
                                  borderRadius: 4,
                                  padding: '2px 6px',
                                  cursor: 'pointer',
                                  color: 'var(--text-tertiary)',
                                  fontSize: '0.65rem',
                                  fontFamily: 'var(--font-sans)',
                                }}
                              >
                                Copy
                              </button>
                            </div>
                            <SyntaxHighlighter
                              style={oneDark}
                              language={match[1]}
                              PreTag="div"
                              customStyle={{
                                borderRadius: 'var(--radius-sm)',
                                fontSize: '0.8rem',
                                margin: 0,
                                padding: '32px 16px 14px',
                              }}
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          </div>
                        );
                      }
                      if (!inline) {
                        return (
                          <SyntaxHighlighter
                            style={oneDark}
                            PreTag="div"
                            customStyle={{
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '0.8rem',
                              margin: 0,
                            }}
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        );
                      }
                      return (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Footer: timestamp + copy */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginTop: 4,
              justifyContent: isUser ? 'flex-end' : 'flex-start',
            }}
          >
            <span
              style={{
                fontSize: '0.65rem',
                color: 'var(--text-tertiary)',
              }}
            >
              {formatTimestamp(message.timestamp)}
            </span>

            {!isUser && message.content && (
              <button
                onClick={copyToClipboard}
                title="Copy response"
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-tertiary)',
                  cursor: 'pointer',
                  padding: 2,
                  fontSize: '0.65rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 3,
                  transition: 'color var(--transition-fast)',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-tertiary)'; }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                Copy
              </button>
            )}
          </div>
        </div>

        {/* User avatar */}
        {isUser && (
          <div style={{ marginTop: 2 }}>
            <UserAvatar size={32} />
          </div>
        )}
      </div>
    </div>
  );
}
