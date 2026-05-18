# src/retrieval/query_generator.py
"""
Multi-Query Generator using Llama-3.1-8B-Instruct via Groq.

Purpose:
    A single user question often misses relevant documents because the
    exact words don't match the indexed text (vocabulary mismatch problem).
    This module generates N semantically diverse re-phrasings of the
    original question so that retrieval covers more angles.

    Example:
        Input:  "laptop won't turn on"
        Output: [
            "laptop does not power on troubleshooting steps",
            "computer fails to start, no display or lights",
            "how to diagnose a laptop with no boot response"
        ]

Why a structured JSON prompt?
    Llama-3.1-8B-Instruct follows instruction format well and can reliably
    output JSON when told explicitly. We parse the JSON and fall back
    gracefully if the model deviates.
"""

import json
import re
from typing import List, Optional

from groq import Groq

from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


# ── Prompt specifically tuned for query expansion on laptop troubleshooting ──

QUERY_GEN_SYSTEM_PROMPT = """You are a search query expansion expert specializing in laptop hardware and software troubleshooting.

Your ONLY task is to generate alternative search queries that will help retrieve relevant troubleshooting documents from a knowledge base.

STRICT OUTPUT RULES:
1. Respond with ONLY a valid JSON object — no explanation, no markdown, no code fences.
2. The JSON must have exactly one key: "queries" — a list of strings.
3. Each query must be a distinct rephrasing that targets a DIFFERENT aspect of the problem (symptoms, component names, error types, repair actions).
4. Queries must be concise (5–15 words), use technical laptop terminology where appropriate.
5. Do NOT repeat the original query verbatim.
6. Do NOT include general questions like "how to fix my laptop" — be specific.

Example output:
{"queries": ["laptop battery not detected bios settings", "power adapter not charging dell xps", "battery drain issue windows power management"]}"""


def build_query_gen_prompt(
    original_question: str,
    conversation_history: str,
    num_queries: int,
) -> str:
    """
    Build the user-turn prompt for the query generator.

    The history block (if present) gives the model enough context to generate
    queries that account for what the user already tried in previous turns.
    """
    history_block = ""
    if conversation_history:
        history_block = f"""CONVERSATION HISTORY (for context only — use it to understand what the user already tried):
{conversation_history}

"""

    return f"""{history_block}ORIGINAL USER QUESTION: {original_question}

Generate exactly {num_queries} alternative search queries that cover different aspects of this laptop troubleshooting problem.

Output ONLY the JSON object:"""


class QueryGenerator:
    """
    Generates N semantically diverse query variants from a single user question.

    Uses Llama-3.1-8B-Instruct with a temperature of 0.6 (slightly creative
    to ensure diversity, but not so high that it hallucinates nonsense).

    Usage:
        generator = QueryGenerator(groq_client)
        queries = generator.generate("My screen goes black randomly", history="...")
        # → ["laptop display randomly blanks out", "screen blackout issue gpu driver", ...]
    """

    # Slightly higher temperature to ensure query diversity
    _TEMPERATURE = 0.6
    # Small token budget — we only need a short JSON list
    _MAX_TOKENS = 256

    def __init__(self, client: Groq):
        self.client = client

    def generate(
        self,
        original_question: str,
        conversation_history: str = "",
        num_queries: Optional[int] = None,
    ) -> List[str]:
        """
        Generate alternative search queries for the given question.

        Args:
            original_question:    The user's original question.
            conversation_history: Formatted string of past turns (may be empty).
            num_queries:          How many queries to generate (default: settings.NUM_QUERIES).

        Returns:
            List of alternative query strings. Falls back to [original_question]
            if parsing fails so the pipeline never crashes.
        """
        num_queries = num_queries or settings.NUM_QUERIES
        logger.info(
            "🔀 Generating {} alternative queries for: '{}'",
            num_queries,
            original_question[:60],
        )

        user_prompt = build_query_gen_prompt(
            original_question, conversation_history, num_queries
        )

        try:
            with timer("Multi-query generation (LLM)"):
                response = self.client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": QUERY_GEN_SYSTEM_PROMPT},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=self._TEMPERATURE,
                    max_tokens=self._MAX_TOKENS,
                )

            raw_output = response.choices[0].message.content.strip()
            logger.debug("Query generator raw output: {}", raw_output)

            queries = self._parse_queries(raw_output, num_queries)
            logger.info("✅ Generated {} alternative queries", len(queries))
            return queries

        except Exception as e:
            logger.error("❌ Query generation failed: {} — using original only", str(e))
            return [original_question]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_queries(self, raw: str, expected_count: int) -> List[str]:
        """
        Parse the LLM's JSON output into a list of strings.

        Strategy:
        1. Try direct JSON parse.
        2. If that fails, extract JSON object with regex (handles extra text).
        3. Validate we got the "queries" key and it's a non-empty list of strings.
        4. On any failure, return [original_question] as safe fallback.
        """
        # Strip markdown fences if model added them despite instructions
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

        # Attempt 1: direct parse
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt 2: extract first {...} block
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                logger.warning("Could not find JSON in query generator output")
                return []
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning("JSON extraction also failed for query generator")
                return []

        queries = data.get("queries", [])
        if not isinstance(queries, list):
            logger.warning("'queries' key is not a list in LLM output")
            return []

        # Keep only non-empty strings, cap at expected_count
        valid = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        return valid[:expected_count]
