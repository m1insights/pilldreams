"""AI module for pilldreams - Gemini-powered chat and explanations."""

from backend.ai.client import AIClient, get_ai_client
from backend.ai.context_builder import ContextBuilder
from backend.ai.prompts import SYSTEM_PROMPTS

__all__ = ['AIClient', 'get_ai_client', 'ContextBuilder', 'SYSTEM_PROMPTS']
