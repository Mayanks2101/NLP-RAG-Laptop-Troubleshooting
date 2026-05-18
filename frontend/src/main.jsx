import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';

// Clear persisted chat store on startup to avoid reusing stale session IDs
// (localStorage key is defined in the zustand persist middleware)
try {
  localStorage.removeItem('laptop-ai-chat-store');
  console.debug('[startup] cleared persisted chat store: laptop-ai-chat-store');
} catch (e) {
  // ignore if unavailable (e.g., SSR or private mode)
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
