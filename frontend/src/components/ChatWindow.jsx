import { useRef, useEffect, useCallback } from 'react';
import useChatStore from '../store/chatStore';
import { sendQuery } from '../api/client';
import { useStreamingText } from '../hooks/useStreamingText';
import { useHeroAnimation } from '../hooks/useGsapAnimations';
import MessageBubble from './MessageBubble';
import InputBox from './InputBox';
import TypingIndicator from './TypingIndicator';
import { BrandLogo, AssistantAvatar } from './BrandLogo';

const SUGGESTED_PROMPTS = [
  'My laptop won\'t turn on after charging overnight',
  'Battery drains quickly even when not in use',
  'Screen flickers when I move the lid',
  'No sound from speakers but headphones work',
];

export default function ChatWindow() {
  const activeChat = useChatStore((s) => s.getActiveChat());
  const activeChatId = useChatStore((s) => s.activeChatId);
  const addMessage = useChatStore((s) => s.addMessage);
  const createChat = useChatStore((s) => s.createChat);
  const setGenerating = useChatStore((s) => s.setGenerating);
  const setLastDebugData = useChatStore((s) => s.setLastDebugData);
  const isGenerating = useChatStore((s) => s.isGenerating);

  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const heroRef = useRef(null);
  const { streamText, cancel: cancelStream } = useStreamingText();

  // Apply smooth staggered animation to the empty state hero.
  useHeroAnimation(heroRef);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [activeChat?.messages?.length, scrollToBottom]);

  // Also scroll during streaming
  useEffect(() => {
    if (isGenerating) {
      const iv = setInterval(scrollToBottom, 100);
      return () => clearInterval(iv);
    }
  }, [isGenerating, scrollToBottom]);

  const handleSend = async (text) => {
    let chatId = activeChatId;
    let sessionId = activeChat?.sessionId;

    // If no active chat, create one
    if (!chatId) {
      chatId = createChat();
      sessionId = useChatStore.getState().getActiveChat()?.sessionId;
    }

    // Add user message
    addMessage(chatId, {
      role: 'user',
      content: text,
      timestamp: Date.now(),
    });

    // Add empty assistant message (will be filled by streaming)
    addMessage(chatId, {
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    });

    setGenerating(true);

    try {
      const response = await sendQuery(text, sessionId);

      // Store debug-relevant data from the regular response
      setLastDebugData({
        question: response.question,
        answer: response.answer,
        generated_queries: response.generated_queries || [],
        chunks_used: response.chunks_used,
        processing_time_seconds: response.processing_time_seconds,
        session_id: response.session_id,
        turn_number: response.turn_number,
      });

      // Stream the response word by word
      streamText(response.answer, chatId, () => {
        setGenerating(false);
      });
    } catch (err) {
      const errorMsg = `⚠️ Error: ${err.message || 'Failed to get response. Is the backend running?'}`;
      useChatStore.getState().updateLastAssistantMessage(chatId, errorMsg);
      setGenerating(false);
    }
  };

  const handleSuggestedPrompt = (prompt) => {
    // Strip the emoji prefix
    const text = prompt.replace(/^[^\w]*/, '').trim();
    handleSend(text);
  };

  // Empty state
  if (!activeChat || activeChat.messages.length === 0) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
        }}
      >
        <div
          ref={heroRef}
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 32,
          }}
        >
          {/* Hero section */}
          <div style={{ marginBottom: 20 }}>
            <BrandLogo size={72} />
          </div>
          <h2
            style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: 8,
              letterSpacing: '-0.02em',
            }}
          >
            Laptop Troubleshooting Assistant
          </h2>
          <p
            style={{
              color: 'var(--text-secondary)',
              fontSize: '0.9rem',
              maxWidth: 420,
              textAlign: 'center',
              lineHeight: 1.6,
              marginBottom: 32,
            }}
          >
            Powered by RAG with multi-query expansion and cross-encoder reranking.
            Ask any laptop hardware or software question.
          </p>

          {/* Suggested prompts */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 10,
              maxWidth: 520,
              width: '100%',
            }}
          >
            {SUGGESTED_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handleSuggestedPrompt(prompt)}
                style={{
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontFamily: 'var(--font-sans)',
                  lineHeight: 1.4,
                  transition: 'all var(--transition-fast)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent)';
                  e.currentTarget.style.background = 'var(--accent-muted)';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border)';
                  e.currentTarget.style.background = 'var(--bg-surface)';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        <InputBox onSend={handleSend} />
      </div>
    );
  }

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minWidth: 0,
      }}
    >
      {/* Messages */}
      <div
        ref={scrollContainerRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px 24px',
        }}
      >
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {activeChat.messages.map((msg, i) => (
            <MessageBubble key={`${activeChat.id}-${i}`} message={msg} />
          ))}

          {/* Typing indicator */}
          {isGenerating && (
            <div style={{ display: 'flex', gap: 10, padding: '6px 0', alignItems: 'flex-start' }}>
              <AssistantAvatar size={32} />
              <div
                style={{
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-lg) var(--radius-lg) var(--radius-lg) 4px',
                  background: 'var(--bg-bubble-assistant)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <TypingIndicator />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <InputBox onSend={handleSend} />
    </div>
  );
}
