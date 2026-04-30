/**
 * API client for the RAG backend.
 * All endpoints proxy through Vite dev server → localhost:8000
 *
 * Supports both advanced (multi-query + reranking) and basic endpoints.
 * Automatically falls back to /query if /advanced_query is not available.
 */

const BASE = '/api/v1';

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.message || `Request failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Send a query — tries /advanced_query first, falls back to /query.
 */
export async function sendQuery(question, sessionId = null) {
  try {
    // Try advanced endpoint first (multi-query + reranking + memory)
    const payload = { question, session_id: sessionId ?? null };
    console.debug('[api] sendQuery payload ->', payload);
    const result = await request(`${BASE}/advanced_query`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return result;
  } catch (err) {
    // If advanced endpoint doesn't exist (404), fall back to basic
    if (err.message.includes('Not Found') || err.message.includes('404')) {
      const result = await request(`${BASE}/query`, {
        method: 'POST',
        body: JSON.stringify({ question }),
      });
      // Normalize response to match advanced format
      return {
        question: result.question,
        answer: result.answer,
        generated_queries: [],
        chunks_used: result.chunks_used || 0,
        processing_time_seconds: result.processing_time_seconds || 0,
        session_id: sessionId,
        turn_number: 1,
      };
    }
    throw err;
  }
}

/**
 * Send a debug query — tries /advanced_query_debug first, falls back to /query_debug.
 */
export async function sendDebugQuery(question, sessionId = null) {
  try {
    const payload = { question, session_id: sessionId ?? null };
    console.debug('[api] sendDebugQuery payload ->', payload);
    return await request(`${BASE}/advanced_query_debug`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  } catch (err) {
    if (err.message.includes('Not Found') || err.message.includes('404')) {
      const result = await request(`${BASE}/query_debug`, {
        method: 'POST',
        body: JSON.stringify({ question }),
      });
      return {
        question: result.question,
        answer: result.answer,
        generated_queries: [],
        chunks_used: result.chunks_used || 0,
        processing_time_seconds: result.processing_time_seconds || 0,
        session_id: null,
        turn_number: 1,
        retrieved_contexts: result.retrieved_contexts || [],
      };
    }
    throw err;
  }
}

/**
 * Clear conversation history for a specific session.
 */
export async function clearSession(sessionId) {
  return request(`${BASE}/session/${sessionId}`, { method: 'DELETE' });
}

/**
 * Check backend health status.
 */
export async function checkHealth() {
  return request(`${BASE}/health`);
}

/**
 * Get collection stats.
 */
export async function getStats() {
  return request(`${BASE}/stats`);
}
