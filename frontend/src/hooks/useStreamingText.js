import { useRef, useCallback } from 'react';
import useChatStore from '../store/chatStore';

/**
 * Custom hook that simulates word-by-word streaming of a complete response.
 * Uses requestAnimationFrame for smooth rendering.
 */
export function useStreamingText() {
  const cancelRef = useRef(false);
  const rafRef = useRef(null);

  const streamText = useCallback((fullText, chatId, onComplete) => {
    cancelRef.current = false;
    const words = fullText.split(/(\s+)/); // preserve whitespace
    let index = 0;
    let accumulated = '';
    const WORDS_PER_TICK = 2;
    const DELAY_MS = 22;

    const tick = () => {
      if (cancelRef.current) return;

      // Add next batch of words
      const end = Math.min(index + WORDS_PER_TICK, words.length);
      for (let i = index; i < end; i++) {
        accumulated += words[i];
      }
      index = end;

      useChatStore.getState().updateLastAssistantMessage(chatId, accumulated);

      if (index < words.length) {
        rafRef.current = setTimeout(() => {
          requestAnimationFrame(tick);
        }, DELAY_MS);
      } else {
        onComplete?.();
      }
    };

    requestAnimationFrame(tick);
  }, []);

  const cancel = useCallback(() => {
    cancelRef.current = true;
    if (rafRef.current) {
      clearTimeout(rafRef.current);
    }
  }, []);

  return { streamText, cancel };
}
