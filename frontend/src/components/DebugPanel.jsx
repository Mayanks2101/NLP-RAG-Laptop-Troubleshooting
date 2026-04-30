import { useRef, useState, useEffect } from 'react';
import useChatStore from '../store/chatStore';
import { sendDebugQuery } from '../api/client';
import { useDebugPanelAnimation } from '../hooks/useGsapAnimations';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

function AccordionSection({ title, icon, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const contentRef = useRef(null);

  return (
    <div
      style={{
        borderBottom: '1px solid var(--border)',
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%',
          padding: '12px 16px',
          background: open ? 'var(--accent-muted)' : 'transparent',
          border: 'none',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.82rem',
          fontWeight: 600,
          fontFamily: 'var(--font-sans)',
          transition: 'all var(--transition-fast)',
        }}
        onMouseEnter={(e) => {
          if (!open) e.currentTarget.style.background = 'var(--bg-hover)';
        }}
        onMouseLeave={(e) => {
          if (!open) e.currentTarget.style.background = 'transparent';
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>{icon}</span>
          {title}
        </span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          style={{
            transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform var(--transition-fast)',
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      <div
        ref={contentRef}
        style={{
          maxHeight: open ? '2000px' : '0',
          overflow: 'hidden',
          transition: 'max-height var(--transition-slow)',
        }}
      >
        <div style={{ padding: '12px 16px' }}>{children}</div>
      </div>
    </div>
  );
}

export default function DebugPanel() {
  const panelRef = useRef(null);
  const debugPanelOpen = useChatStore((s) => s.debugPanelOpen);
  const closeDebugPanel = useChatStore((s) => s.closeDebugPanel);
  const lastDebugData = useChatStore((s) => s.lastDebugData);
  const activeChat = useChatStore((s) => s.getActiveChat());

  const [fullDebugData, setFullDebugData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('structured'); // 'structured' | 'json'

  useDebugPanelAnimation(panelRef, debugPanelOpen);

  // Fetch full debug data when panel opens and we have a last question
  useEffect(() => {
    if (!debugPanelOpen || !lastDebugData?.question) return;

    const fetchDebug = async () => {
      setLoading(true);
      try {
        const result = await sendDebugQuery(
          lastDebugData.question,
          activeChat?.sessionId ?? null  // Pass session_id for conversation context
        );
        setFullDebugData(result);
      } catch (err) {
        console.error('Debug query failed:', err);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch if we don't already have retrieved_contexts
    if (!fullDebugData || fullDebugData.question !== lastDebugData.question) {
      fetchDebug();
    }
  }, [debugPanelOpen, lastDebugData?.question]);

  const debugData = fullDebugData || lastDebugData;

  if (!debugPanelOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={closeDebugPanel}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.4)',
          zIndex: 40,
          backdropFilter: 'blur(2px)',
        }}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        id="debug-panel"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          width: 'min(var(--debug-panel-width), 90vw)',
          height: '100vh',
          background: 'var(--bg-panel)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          borderLeft: 'var(--glass-border)',
          zIndex: 50,
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--shadow-lg)',
          transform: 'translateX(100%)',
          opacity: 0,
        }}
      >
        {/* Panel header */}
        <div
          style={{
            padding: '14px 16px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          <div>
            <h2
              style={{
                fontSize: '0.95rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                <path d="M12 16v-4" />
                <path d="M12 8h.01" />
              </svg>
              RAG Pipeline Debug
            </h2>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginTop: 2 }}>
              Inspect the full retrieval & generation pipeline
            </p>
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {/* View mode toggle */}
            <div
              style={{
                display: 'flex',
                background: 'var(--bg-hover)',
                borderRadius: 'var(--radius-sm)',
                overflow: 'hidden',
                border: '1px solid var(--border)',
              }}
            >
              {['structured', 'json'].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  style={{
                    padding: '4px 10px',
                    fontSize: '0.7rem',
                    fontWeight: 500,
                    fontFamily: 'var(--font-sans)',
                    border: 'none',
                    cursor: 'pointer',
                    background: viewMode === mode ? 'var(--accent)' : 'transparent',
                    color: viewMode === mode ? '#fff' : 'var(--text-secondary)',
                    transition: 'all var(--transition-fast)',
                    textTransform: 'capitalize',
                  }}
                >
                  {mode}
                </button>
              ))}
            </div>

            <button
              onClick={closeDebugPanel}
              style={{
                background: 'var(--bg-hover)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                width: 32,
                height: 32,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-secondary)',
                transition: 'all var(--transition-fast)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--error)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        {/* Panel content */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {loading && (
            <div
              style={{
                padding: 32,
                textAlign: 'center',
                color: 'var(--text-tertiary)',
                fontSize: '0.85rem',
              }}
            >
              <div style={{ marginBottom: 12, fontSize: 24 }}>⏳</div>
              Fetching pipeline debug data…
            </div>
          )}

          {!debugData && !loading && (
            <div
              style={{
                padding: 32,
                textAlign: 'center',
                color: 'var(--text-tertiary)',
                fontSize: '0.85rem',
              }}
            >
              <div style={{ marginBottom: 12, fontSize: 24 }}>🔍</div>
              Send a query first to see pipeline debug data here.
            </div>
          )}

          {debugData && !loading && viewMode === 'json' && (
            <div style={{ padding: 16 }}>
              <SyntaxHighlighter
                language="json"
                style={oneDark}
                customStyle={{
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  margin: 0,
                }}
              >
                {JSON.stringify(debugData, null, 2)}
              </SyntaxHighlighter>
            </div>
          )}

          {debugData && !loading && viewMode === 'structured' && (
            <div>
              {/* Pipeline stats summary */}
              <div
                style={{
                  padding: '14px 16px',
                  borderBottom: '1px solid var(--border)',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: 10,
                }}
              >
                {[
                  { label: 'Processing', value: `${debugData.processing_time_seconds}s`, color: 'var(--accent)' },
                  { label: 'Chunks Used', value: debugData.chunks_used, color: 'var(--success)' },
                  { label: 'Turn #', value: debugData.turn_number || 1, color: 'var(--warning)' },
                ].map((stat, i) => (
                  <div
                    key={i}
                    style={{
                      textAlign: 'center',
                      padding: '8px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: stat.color }}>
                      {stat.value}
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginTop: 2 }}>
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>

              {/* 1: Conversation History */}
              <AccordionSection title="Conversation History" icon="🧾" defaultOpen={false}>
                {activeChat?.messages?.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {activeChat.messages.map((msg, i) => (
                      <div
                        key={i}
                        style={{
                          padding: '8px 10px',
                          borderRadius: 'var(--radius-sm)',
                          background: msg.role === 'user' ? 'var(--accent-muted)' : 'var(--bg-surface)',
                          border: '1px solid var(--border-subtle)',
                          fontSize: '0.78rem',
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: '0.7rem', color: msg.role === 'user' ? 'var(--accent)' : 'var(--success)', marginBottom: 4, textTransform: 'uppercase' }}>
                          {msg.role}
                        </div>
                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.5, whiteSpace: 'pre-wrap', maxHeight: 120, overflow: 'auto' }}>
                          {msg.content?.slice(0, 300)}{msg.content?.length > 300 ? '…' : ''}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>No history yet</div>
                )}
              </AccordionSection>

              {/* 2: Generated Queries */}
              <AccordionSection title="Multi-Generated Queries" icon="🔍" defaultOpen={true}>
                {debugData.generated_queries?.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div
                      style={{
                        padding: '8px 10px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--accent-muted)',
                        border: '1px solid var(--accent)',
                        fontSize: '0.78rem',
                        color: 'var(--accent)',
                        fontWeight: 500,
                      }}
                    >
                      <span style={{ fontWeight: 600, fontSize: '0.68rem', opacity: 0.7 }}>ORIGINAL → </span>
                      {debugData.question}
                    </div>
                    {debugData.generated_queries.map((q, i) => (
                      <div
                        key={i}
                        style={{
                          padding: '8px 10px',
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border-subtle)',
                          fontSize: '0.78rem',
                          color: 'var(--text-secondary)',
                          display: 'flex',
                          gap: 8,
                          alignItems: 'flex-start',
                        }}
                      >
                        <span
                          style={{
                            background: 'var(--bg-hover)',
                            borderRadius: 4,
                            padding: '1px 6px',
                            fontSize: '0.65rem',
                            fontWeight: 600,
                            color: 'var(--text-tertiary)',
                            flexShrink: 0,
                          }}
                        >
                          Q{i + 1}
                        </span>
                        {q}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>No generated queries</div>
                )}
              </AccordionSection>

              {/* 3: Retrieved Documents */}
              <AccordionSection title="Retrieved Documents" icon="📚" defaultOpen={false}>
                {fullDebugData?.retrieved_contexts?.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {fullDebugData.retrieved_contexts.map((ctx, i) => (
                      <div
                        key={i}
                        style={{
                          padding: '10px 12px',
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border-subtle)',
                          fontSize: '0.78rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.75rem' }}>
                            Chunk {i + 1}
                          </span>
                          <span
                            style={{
                              fontSize: '0.65rem',
                              padding: '1px 8px',
                              borderRadius: 'var(--radius-full)',
                              background: 'var(--accent-muted)',
                              color: 'var(--accent)',
                              fontWeight: 500,
                            }}
                          >
                            {ctx.source || 'unknown'}
                          </span>
                        </div>
                        <div
                          style={{
                            color: 'var(--text-secondary)',
                            lineHeight: 1.5,
                            whiteSpace: 'pre-wrap',
                            maxHeight: 150,
                            overflow: 'auto',
                            fontSize: '0.75rem',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {ctx.text?.slice(0, 500)}{ctx.text?.length > 500 ? '…' : ''}
                        </div>
                        <div
                          style={{
                            display: 'flex',
                            gap: 12,
                            marginTop: 8,
                            fontSize: '0.65rem',
                            color: 'var(--text-tertiary)',
                          }}
                        >
                          {ctx.score !== undefined && (
                            <span>Bi-Encoder: <strong style={{ color: 'var(--warning)' }}>{Number(ctx.score).toFixed(4)}</strong></span>
                          )}
                          {ctx.reranker_score !== undefined && (
                            <span>Reranker: <strong style={{ color: 'var(--success)' }}>{Number(ctx.reranker_score).toFixed(4)}</strong></span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                    {loading ? 'Loading…' : 'No retrieved documents available. Open the debug panel after sending a query.'}
                  </div>
                )}
              </AccordionSection>

              {/* 4: Reranker Scores */}
              <AccordionSection title="Reranker Scores & Final Chunks" icon="🧠" defaultOpen={false}>
                {fullDebugData?.retrieved_contexts?.length > 0 ? (
                  <div>
                    <div
                      style={{
                        fontSize: '0.72rem',
                        color: 'var(--text-tertiary)',
                        marginBottom: 10,
                      }}
                    >
                      Sorted by reranker score (highest first):
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {[...fullDebugData.retrieved_contexts]
                        .sort((a, b) => (b.reranker_score || 0) - (a.reranker_score || 0))
                        .map((ctx, i) => (
                          <div
                            key={i}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 10,
                              padding: '8px 10px',
                              borderRadius: 'var(--radius-sm)',
                              background: i === 0 ? 'rgba(34,197,94,0.08)' : 'var(--bg-surface)',
                              border: `1px solid ${i === 0 ? 'rgba(34,197,94,0.2)' : 'var(--border-subtle)'}`,
                              fontSize: '0.75rem',
                            }}
                          >
                            <span
                              style={{
                                fontWeight: 700,
                                color: i === 0 ? 'var(--success)' : 'var(--text-tertiary)',
                                fontSize: '0.85rem',
                                minWidth: 24,
                              }}
                            >
                              #{i + 1}
                            </span>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {ctx.text?.slice(0, 80)}…
                              </div>
                              <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginTop: 2 }}>
                                {ctx.source}
                              </div>
                            </div>
                            <div
                              style={{
                                fontWeight: 700,
                                fontSize: '0.82rem',
                                color: 'var(--accent)',
                                fontFamily: 'var(--font-mono)',
                                flexShrink: 0,
                              }}
                            >
                              {ctx.reranker_score !== undefined ? Number(ctx.reranker_score).toFixed(3) : 'N/A'}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>No reranker data available</div>
                )}
              </AccordionSection>

              {/* 5: Final Answer */}
              <AccordionSection title="Final LLM Response" icon="🧩" defaultOpen={false}>
                <div
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.78rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap',
                    maxHeight: 300,
                    overflow: 'auto',
                  }}
                >
                  {debugData.answer || 'No response yet'}
                </div>
              </AccordionSection>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
