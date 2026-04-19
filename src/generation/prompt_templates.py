# src/generation/prompt_templates.py
"""
Prompt engineering module.

Defines the system instructions, fallback messages, and dynamic prompt builder.
Well-crafted prompts are CRITICAL for RAG quality. They prevent hallucinations
and enforce grounding in retrieved context.

Beginner tip: Think of the prompt as "instructions to the AI". 
Be explicit about what it SHOULD and SHOULD NOT do.
"""

from typing import List, Dict


# System Prompt: Sets the AI's persona & rules
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

# Fallback: Used when retrieval finds nothing relevant
FALLBACK_RESPONSE = "I couldn't find specific troubleshooting steps for this issue in the uploaded manuals. Please verify your laptop model, try rephrasing your question, or consult the manufacturer's official support site."


def build_prompt(question: str, contexts: List[Dict]) -> str:
    """
    Assemble the final prompt by combining context and question.
    
    Args:
        question: User's original query
        contexts: List of retrieved chunks from Qdrant
        
    Returns:
        Formatted string ready for LLM
    """
    # Join contexts with clear separators for readability
    context_block = "\n\n---\n\n".join([
        f"[Source: {ctx['source']}]\n{ctx['text']}" 
        for ctx in contexts
    ])
    
    return f"""📖 CONTEXT INFORMATION:
{context_block}

❓ USER QUESTION: {question}

🛠️ Provide a step-by-step troubleshooting answer based strictly on the context above:"""