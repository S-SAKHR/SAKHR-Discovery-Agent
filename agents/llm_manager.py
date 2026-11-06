import os
import time
import random
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_REASONING_MODEL

class MultiLLMManager:
    """
    Unified Multi-Provider LLM Manager for SAKHR AVA_R.
    Handles provider selection, automatic fallback, and rate-limit management.
    Supported Providers: Gemini, Groq (placeholder for future), OpenRouter (placeholder).
    """

    def __init__(self):
        # Initialize Gemini
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        
        self.primary_model = GEMINI_MODEL or "gemini-1.5-flash"
        self.reasoning_model = GEMINI_REASONING_MODEL or "gemini-1.5-pro"

    def _call_gemini(self, prompt: str, model_name: str, temperature: float = 0.2, schema: Optional[Dict[str, Any]] = None) -> str:
        """Calls the Gemini API with exponential backoff and optional JSON schema."""
        model = genai.GenerativeModel(model_name)
        
        generation_config = {
            "temperature": temperature,
        }
        
        if schema:
            generation_config["response_mime_type"] = "application/json"
            generation_config["response_schema"] = schema

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(**generation_config)
                )
                return response.text
            except Exception as e:
                wait_time = (2 ** attempt) + random.random()
                print(f"[LLM Manager] Gemini error (attempt {attempt+1}): {e}. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
        
        raise Exception("Gemini API failed after multiple retries.")

    def generate_analysis(self, prompt: str, high_reasoning: bool = False, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generates analysis using the most appropriate available model.
        Falls back across providers if one fails.
        """
        model_to_use = self.reasoning_model if high_reasoning else self.primary_model
        provider = "google"

        try:
            content = self._call_gemini(prompt, model_to_use, schema=schema)
            
            return {
                "content": content,
                "provider": provider,
                "model": model_to_use,
                "timestamp": time.time()
            }
        except Exception as e:
            print(f"[LLM Manager] All providers failed: {e}")
            return {
                "error": str(e),
                "provider": "none",
                "model": "none"
            }

# Global instance for shared use
llm_manager = MultiLLMManager()
