# src/generation/prompt_templates.py
"""
Prompt engineering module — updated for advanced RAG pipeline.

Contains THREE purpose-built prompts, each tuned for a specific task:

1. QUERY_GEN_SYSTEM_PROMPT  (in query_generator.py)
   → Generates diverse search queries from the original question.
   → Kept in query_generator.py for locality with that class.

2. FINAL_ANSWER_SYSTEM_PROMPT  (here)
   → Synthesizes the final answer from history + all queries + reranked chunks.
   → Tuned for step-by-step troubleshooting with source citations.

3. FALLBACK_RESPONSE  (here)
   → Returned when retrieval finds nothing relevant.

Design philosophy:
- Each prompt tells the model EXACTLY what role it plays, what it
  has access to, and what it must NOT do (no hallucination).
- Format instructions are explicit: numbered steps, source citations,
  safety-first ordering.
- The final answer prompt is aware of history so the model can say
  "Since you already tried X in our previous conversation..." naturally.
"""

from typing import List, Dict


# ===========================================================================
# PROMPT 2: Final Answer Synthesizer
# Used in: AdvancedQAPipeline → GroqLLMClient.generate()
# ===========================================================================

FINAL_ANSWER_SYSTEM_PROMPT = """You are an expert laptop hardware and software technician with deep field experience across all major brands (Dell, HP, Lenovo, ASUS, Apple, Acer, MSI).

You are helping a user diagnose and fix their laptop problem through a conversation.

## What you have access to:
- CONVERSATION HISTORY: Previous turns of this troubleshooting session.
- GENERATED QUERIES: The search angles used to find relevant documentation.
- RETRIEVED CONTEXT: Excerpts from official laptop manuals and guides — this is your ONLY knowledge source.

## STRICT RULES — follow these without exception:
1. Base your answer EXCLUSIVELY on the RETRIEVED CONTEXT. Do NOT use outside knowledge.
2. If the context does not cover the issue, say exactly: "The available manuals don't cover this specific issue. Please consult your laptop model's official support page."
3. ALWAYS acknowledge prior conversation: if the user already tried something (visible in HISTORY), skip it or build upon it — never repeat advice they've already followed.
4. Format answers as clear numbered steps. For multi-component issues, use sub-steps (1a, 1b, etc.).
5. Always start with the SAFEST action first (e.g., power off, unplug) if safety steps appear in the context.
6. Cite the source manual after each step using [Source: filename].
7. Keep language simple and jargon-free for non-technical users.
8. End with a follow-up question like "Did that resolve the issue?" to continue the troubleshooting loop."""


# ===========================================================================
# FALLBACK: When retrieval finds nothing
# ===========================================================================

FALLBACK_RESPONSE = (
    "I couldn't find specific troubleshooting steps for this issue in the uploaded manuals. "
    "This could mean:\n"
    "• The topic isn't covered in the indexed documents.\n"
    "• Try rephrasing — for example, describe the symptom rather than the cause.\n"
    "• Consult your laptop manufacturer's official support page for model-specific guidance."
)


# ===========================================================================
# Prompt builders
# ===========================================================================

def build_final_answer_prompt(
    original_question: str,
    generated_queries: List[str],
    reranked_chunks: List[Dict],
    conversation_history: str = "",
) -> str:
    """
    Build the user-turn prompt for the final answer synthesizer.

    Args:
        original_question: The user's exact question this turn.
        generated_queries: List of alternative queries used for retrieval.
        reranked_chunks:   Top-K chunks after reranking (each has text, source, reranker_score).
        conversation_history: Formatted multi-turn history string (may be empty for first turn).

    Returns:
        A structured prompt string ready to send as the "user" role to the LLM.
    """
    # ── Section 1: Conversation History ──────────────────────────────────────
    history_block = ""
    if conversation_history:
        history_block = f"""## 📜 CONVERSATION HISTORY
{conversation_history}

"""

    # ── Section 2: Generated Queries ─────────────────────────────────────────
    query_list = "\n".join(
        f"  {i + 1}. {q}" for i, q in enumerate(generated_queries)
    )
    queries_block = f"""## 🔍 SEARCH QUERIES USED FOR RETRIEVAL
  Original: {original_question}
{query_list}

"""

    # ── Section 3: Retrieved Context ─────────────────────────────────────────
    context_parts = []
    for i, chunk in enumerate(reranked_chunks, 1):
        score_info = f"[Relevance: {chunk.get('reranker_score', 'N/A')}]"
        context_parts.append(
            f"--- Chunk {i} {score_info} ---\n"
            f"[Source: {chunk['source']}]\n"
            f"{chunk['text']}"
        )
    context_block = f"""## 📖 RETRIEVED CONTEXT (from laptop manuals)
{chr(10).join(context_parts)}

"""

    # ── Section 4: The actual question ───────────────────────────────────────
    question_block = f"""## ❓ CURRENT USER QUESTION
{original_question}

## 🛠️ YOUR TASK
Using ONLY the retrieved context above, provide a clear, step-by-step troubleshooting answer.
Take into account the conversation history — do not repeat steps the user has already performed.
End with a follow-up question to continue the troubleshooting session."""

    return history_block + queries_block + context_block + question_block


# Keep the old build_prompt for backward compatibility with the simple /query endpoint
def build_prompt(question: str, contexts: List[Dict]) -> str:
    """
    Legacy prompt builder for the simple (non-advanced) /query endpoint.
    Kept for backward compatibility — does not include history or multi-query info.
    """
    context_block = "\n\n---\n\n".join([
        f"[Source: {ctx['source']}]\n{ctx['text']}"
        for ctx in contexts
    ])

    return f"""📖 CONTEXT INFORMATION:
{context_block}

❓ USER QUESTION: {question}

🛠️ Provide a step-by-step troubleshooting answer based strictly on the context above:"""


# Legacy system prompt for the simple /query endpoint
SYSTEM_PROMPT = """You are an expert laptop troubleshooting technician with years of field experience.
Your task is to provide clear, actionable, step-by-step solutions based STRICTLY on the provided context.

🔒 STRICT RULES:
1. Use ONLY the provided context. Do NOT invent steps or rely on outside knowledge.
2. If the context doesn't cover the issue, respond exactly with: "The uploaded manuals don't cover this specific issue. Please check your laptop model's official support documentation."
3. Always start with safety checks (power cable, battery removal, etc.) if mentioned in context.
4. Format answers as numbered steps when applicable.
5. Keep responses concise, professional, and easy to follow for non-technical users.
6. Cite source manuals using [Source: filename] when helpful.
"""