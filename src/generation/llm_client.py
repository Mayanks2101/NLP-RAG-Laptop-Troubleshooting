# src/generation/llm_client.py
"""
Groq LLM client wrapper with retry logic & timing.

Handles API calls to Llama-3.1-8b-instant via Groq.
Includes automatic retries for rate limits and network hiccups.

Beginner tip: External APIs fail sometimes. Retries + timeouts prevent
your whole pipeline from crashing over a temporary network blip.
"""

import time
from typing import Optional
from groq import Groq, APIError, RateLimitError

from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


class GroqLLMClient:
    """
    Manages communication with Groq API for text generation.
    
    Usage:
        llm = GroqLLMClient(groq_client)
        answer = llm.generate(system_prompt, user_prompt)
    """
    
    def __init__(self, client: Groq):
        self.client = client
        
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        max_retries: int = 2
    ) -> str:
        """
        Generate answer with automatic retry on failure.
        
        Args:
            system_prompt: AI persona & rules
            user_prompt: Context + question
            max_retries: Number of retry attempts on error
            
        Returns:
            Generated answer string
        """
        start_time = time.time()
        
        for attempt in range(max_retries + 1):
            try:
                with timer("Groq LLM generation"):
                    response = self.client.chat.completions.create(
                        model=settings.LLM_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=settings.LLM_TEMPERATURE,
                        max_tokens=settings.LLM_MAX_TOKENS
                    )
                
                elapsed = time.time() - start_time
                logger.info(f"✅ LLM response generated in {elapsed:.2f}s")
                return response.choices[0].message.content.strip()
                
            except RateLimitError as e:
                # Exponential backoff: 1s, 2s, 4s...
                wait_time = 2 ** attempt
                logger.warning(f"⏳ Rate limit hit. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                
            except APIError as e:
                logger.error(f"❌ Groq API error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if attempt == max_retries:
                    raise RuntimeError(f"LLM generation failed after {max_retries + 1} attempts: {e}")
                time.sleep(1)  # Brief pause before retry
                
            except Exception as e:
                logger.error(f"❌ Unexpected LLM error: {e}")
                if attempt == max_retries:
                    raise RuntimeError(f"Unexpected LLM failure: {e}")
                time.sleep(1)
                
        # Fallback (should never reach here due to raises above)
        logger.warning("LLM generation returned empty after retries")
        return ""
    

# Expected response format:
# response = {
#     "choices": [
#         {
#             "message": {
#                 "content": "Generated answer string"
#             }
#         }
#     ]
# }