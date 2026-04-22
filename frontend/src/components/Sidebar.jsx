import { useRef, useState } from 'react';
import useChatStore from '../store/chatStore';
import { useSidebarAnimation } from '../hooks/useGsapAnimations';

function timeAgo(ts) {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function Sidebar() {
  const chats = useChatStore((s) => s.chats);
  const activeChatId = useChatStore((s) => s.activeChatId);
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const createChat = useChatStore((s) => s.createChat);
  const deleteChat = useChatStore((s) => s.deleteChat);
  const renameChat = useChatStore((s) => s.renameChat);
  const setActiveChat = useChatStore((s) => s.setActiveChat);

  const listRef = useRef(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [menuOpenId, setMenuOpenId] = useState(null);

  useSidebarAnimation(listRef, [chats.length]);

  const startRename = (chat) => {
    setEditingId(chat.id);
    setEditValue(chat.title);
    setMenuOpenId(null);
  };

  const commitRename = () => {
    if (editingId && editValue.trim()) {
      renameChat(editingId, editValue.trim());
    }
    setEditingId(null);
    setEditValue('');
  };

  const handleDelete = (chatId) => {
    setMenuOpenId(null);
    deleteChat(chatId);
  };

  return (
    <aside
      id="sidebar"
      style={{
        width: sidebarOpen ? 'var(--sidebar-width)' : 0,
        minWidth: sidebarOpen ? 'var(--sidebar-width)' : 0,
        height: '100%',
        background: 'var(--bg-secondary)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        borderRight: sidebarOpen ? 'var(--glass-border)' : 'none',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'width var(--transition-slow), min-width var(--transition-slow)',
        flexShrink: 0,
      }}
    >
      {/* New chat button */}
      <div style={{ padding: '16px 14px 8px' }}>
        <button
          id="new-chat-btn"
          onClick={createChat}
          style={{
            width: '100%',
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--border)',
            background: 'transparent',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: '0.85rem',
            fontWeight: 500,
            fontFamily: 'var(--font-sans)',
            transition: 'all var(--transition-fast)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent)';
            e.currentTarget.style.color = 'var(--accent)';
            e.currentTarget.style.background = 'var(--accent-muted)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border)';
            e.currentTarget.style.color = 'var(--text-secondary)';
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Section label */}
      <div
        style={{
          padding: '8px 16px 4px',
          fontSize: '0.68rem',
          fontWeight: 600,
          color: 'var(--text-tertiary)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}
      >
        Chat History
      </div>

      {/* Chat list */}
      <div
        ref={listRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '4px 8px',
        }}
      >
        {chats.length === 0 && (
          <div
            style={{
              padding: '24px 16px',
              textAlign: 'center',
              color: 'var(--text-tertiary)',
              fontSize: '0.8rem',
            }}
          >
            No chats yet. Start a new one!
          </div>
        )}

        {chats.map((chat) => {
          const isActive = chat.id === activeChatId;
          const isEditing = editingId === chat.id;

          return (
            <div
              key={chat.id}
              className="sidebar-chat-item"
              onClick={() => {
                if (!isEditing) setActiveChat(chat.id);
                setMenuOpenId(null);
              }}
              style={{
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                marginBottom: 2,
                background: isActive ? 'var(--accent-muted)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                transition: 'all var(--transition-fast)',
                position: 'relative',
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = 'var(--bg-hover)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
                // Don't close menu on leave — let click outside handle it
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {isEditing ? (
                    <input
                      autoFocus
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={commitRename}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') commitRename();
                        if (e.key === 'Escape') setEditingId(null);
                      }}
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        width: '100%',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--accent)',
                        borderRadius: 4,
                        padding: '2px 6px',
                        color: 'var(--text-primary)',
                        fontSize: '0.82rem',
                        fontFamily: 'var(--font-sans)',
                        outline: 'none',
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        fontSize: '0.84rem',
                        fontWeight: isActive ? 600 : 500,
                        color: isActive ? 'var(--accent)' : 'var(--text-primary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {chat.title}
                    </div>
                  )}
                  {chat.subtitle && !isEditing && (
                    <div
                      style={{
                        fontSize: '0.72rem',
                        color: 'var(--text-tertiary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        marginTop: 2,
                      }}
                    >
                      {chat.subtitle}
                    </div>
                  )}
                </div>

                {/* Three-dot menu */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpenId(menuOpenId === chat.id ? null : chat.id);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-tertiary)',
                    cursor: 'pointer',
                    padding: 2,
                    borderRadius: 4,
                    opacity: isActive || menuOpenId === chat.id ? 1 : 0,
                    transition: 'opacity var(--transition-fast)',
                    flexShrink: 0,
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="5" r="2" />
                    <circle cx="12" cy="12" r="2" />
                    <circle cx="12" cy="19" r="2" />
                  </svg>
                </button>
              </div>

              {/* Timestamp */}
              {!isEditing && (
                <div
                  style={{
                    fontSize: '0.65rem',
                    color: 'var(--text-tertiary)',
                    marginTop: 4,
                  }}
                >
                  {timeAgo(chat.createdAt)}
                </div>
              )}

              {/* Dropdown menu */}
              {menuOpenId === chat.id && (
                <div
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: 8,
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    boxShadow: 'var(--shadow-lg)',
                    zIndex: 50,
                    overflow: 'hidden',
                    minWidth: 120,
                    animation: 'fadeInUp 0.15s ease-out',
                  }}
                >
                  <button
                    onClick={() => startRename(chat)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-secondary)',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontFamily: 'var(--font-sans)',
                      transition: 'background var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-hover)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
                  >
                    ✏️ Rename
                  </button>
                  <button
                    onClick={() => handleDelete(chat.id)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      background: 'none',
                      border: 'none',
                      color: 'var(--error)',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontFamily: 'var(--font-sans)',
                      transition: 'background var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(239,68,68,0.08)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
                  >
                    🗑️ Delete
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border)',
          fontSize: '0.68rem',
          color: 'var(--text-tertiary)',
          textAlign: 'center',
        }}
      >
        Powered by RAG Pipeline
      </div>
    </aside>
  );
}
