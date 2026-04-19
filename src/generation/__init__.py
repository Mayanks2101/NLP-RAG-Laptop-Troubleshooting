# src/generation/__init__.py
"""Generation module: Handles prompt engineering & LLM answer generation."""
from .llm_client import GroqLLMClient
from .prompt_templates import SYSTEM_PROMPT, FALLBACK_RESPONSE, build_prompt
from .qa_chain import QAPipeline
__all__ = ["GroqLLMClient", "SYSTEM_PROMPT", "FALLBACK_RESPONSE", "build_prompt", "QAPipeline"]