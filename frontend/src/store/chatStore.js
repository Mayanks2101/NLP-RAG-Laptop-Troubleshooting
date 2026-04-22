import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';

const useChatStore = create(
  persist(
    (set, get) => ({
      /* ── State ────────────────────────────────────────────── */
      chats: [],
      activeChatId: null,
      theme: 'dark',
      isGenerating: false,
      debugPanelOpen: false,
      sidebarOpen: true,
      lastDebugData: null,

      /* ── Chat CRUD ────────────────────────────────────────── */

      createChat: () => {
        const newChat = {
          id: uuidv4(),
          sessionId: uuidv4(),
          title: 'New Chat',
          subtitle: '',
          messages: [],
          createdAt: Date.now(),
        };
        set((state) => ({
          chats: [newChat, ...state.chats],
          activeChatId: newChat.id,
        }));
        return newChat.id;
      },

      deleteChat: (chatId) => {
        set((state) => {
          const filtered = state.chats.filter((c) => c.id !== chatId);
          const newActive =
            state.activeChatId === chatId
              ? filtered.length > 0
                ? filtered[0].id
                : null
              : state.activeChatId;
          return { chats: filtered, activeChatId: newActive };
        });
      },

      renameChat: (chatId, newTitle) => {
        set((state) => ({
          chats: state.chats.map((c) =>
            c.id === chatId ? { ...c, title: newTitle } : c
          ),
        }));
      },

      setActiveChat: (chatId) => set({ activeChatId: chatId }),

      /* ── Messages ─────────────────────────────────────────── */

      addMessage: (chatId, message) => {
        set((state) => ({
          chats: state.chats.map((c) => {
            if (c.id !== chatId) return c;
            const updated = {
              ...c,
              messages: [...c.messages, message],
            };
            // Auto-generate subtitle from first user message
            if (!c.subtitle && message.role === 'user') {
              updated.subtitle = message.content.slice(0, 60) + (message.content.length > 60 ? '…' : '');
            }
            return updated;
          }),
        }));
      },

      updateLastAssistantMessage: (chatId, content) => {
        set((state) => ({
          chats: state.chats.map((c) => {
            if (c.id !== chatId) return c;
            const msgs = [...c.messages];
            // Find last assistant message
            for (let i = msgs.length - 1; i >= 0; i--) {
              if (msgs[i].role === 'assistant') {
                msgs[i] = { ...msgs[i], content };
                break;
              }
            }
            return { ...c, messages: msgs };
          }),
        }));
      },

      setMessageDebugData: (chatId, messageIndex, debugData) => {
        set((state) => ({
          chats: state.chats.map((c) => {
            if (c.id !== chatId) return c;
            const msgs = [...c.messages];
            if (msgs[messageIndex]) {
              msgs[messageIndex] = { ...msgs[messageIndex], debugData };
            }
            return { ...c, messages: msgs };
          }),
        }));
      },

      /* ── UI Toggles ───────────────────────────────────────── */

      setGenerating: (val) => set({ isGenerating: val }),

      toggleTheme: () => {
        set((state) => {
          const next = state.theme === 'dark' ? 'light' : 'dark';
          document.documentElement.setAttribute('data-theme', next);
          return { theme: next };
        });
      },

      toggleDebugPanel: () => set((state) => ({ debugPanelOpen: !state.debugPanelOpen })),
      closeDebugPanel: () => set({ debugPanelOpen: false }),

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      setLastDebugData: (data) => set({ lastDebugData: data }),

      /* ── Selectors ────────────────────────────────────────── */

      getActiveChat: () => {
        const state = get();
        return state.chats.find((c) => c.id === state.activeChatId) || null;
      },
    }),
    {
      name: 'laptop-ai-chat-store',
      // Only persist chats, activeChatId, and theme
      partialize: (state) => ({
        chats: state.chats,
        activeChatId: state.activeChatId,
        theme: state.theme,
      }),
      onRehydrate: (_state) => {
        // This runs BEFORE state is hydrated (return a function for AFTER)
        return (state) => {
          if (state?.theme) {
            document.documentElement.setAttribute('data-theme', state.theme);
          }
        };
      },
    }
  )
);

export default useChatStore;
