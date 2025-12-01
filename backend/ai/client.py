"""
AI Client - Model-agnostic abstraction for LLM interactions.

Currently supports Gemini, but designed to easily swap to GPT/Claude.
"""
import os
import json
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class AIClient(ABC):
    """Abstract base class for AI clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate a response from the AI model."""
        pass

    @abstractmethod
    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate a response with conversation history."""
        pass


class GeminiClient(AIClient):
    """Gemini AI client implementation."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Initialize Gemini client.

        Args:
            model_name: Gemini model to use. Options:
                - "gemini-2.0-flash" (fast, cheap, good for explanations)
                - "gemini-1.5-pro" (more capable, higher cost)
        """
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def _build_prompt(
        self,
        user_prompt: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the full prompt with system instructions and context."""
        parts = [system_prompt]

        if context:
            parts.append("\n## Database Context (use ONLY this data for specific facts):\n")
            parts.append("```json")
            parts.append(json.dumps(context, indent=2, default=str))
            parts.append("```")

        parts.append(f"\n## User Question:\n{user_prompt}")

        return "\n".join(parts)

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate a response from Gemini."""
        full_prompt = self._build_prompt(prompt, system_prompt, context)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate a response with conversation history."""
        # Build conversation for Gemini
        history = []

        # Add system prompt as first user message (Gemini doesn't have system role)
        context_block = ""
        if context:
            context_block = f"\n\n## Database Context:\n```json\n{json.dumps(context, indent=2, default=str)}\n```"

        # Convert message history to Gemini format
        for i, msg in enumerate(messages[:-1]):  # All but last message
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]
            if i == 0 and role == "user":
                # Prepend system prompt to first user message
                content = f"{system_prompt}{context_block}\n\nUser: {content}"
            history.append({"role": role, "parts": [content]})

        # Start chat with history
        chat = self.model.start_chat(history=history)

        # Send the last message
        last_message = messages[-1]["content"]
        if not history:
            # No history, include system prompt
            last_message = f"{system_prompt}{context_block}\n\nUser: {last_message}"

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        try:
            response = chat.send_message(
                last_message,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"


class MockAIClient(AIClient):
    """Mock AI client for testing without API calls."""

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Return a mock response."""
        if context:
            entities = []
            if "drugs" in context:
                entities.extend([d.get("name", "Unknown") for d in context["drugs"]])
            if "targets" in context:
                entities.extend([t.get("symbol", "Unknown") for t in context["targets"]])

            return f"[Mock Response] Analyzing: {', '.join(entities[:3])}. This is a test response based on the provided context."
        return f"[Mock Response] Received question: {prompt[:100]}..."

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Return a mock response with history context."""
        last_msg = messages[-1]["content"] if messages else "No message"
        return f"[Mock Response] Conversation with {len(messages)} messages. Last: {last_msg[:50]}..."


# Singleton instance
_ai_client: Optional[AIClient] = None


def get_ai_client(use_mock: bool = False) -> AIClient:
    """
    Get the AI client singleton.

    Args:
        use_mock: If True, return mock client (for testing)

    Returns:
        AIClient instance
    """
    global _ai_client

    if use_mock:
        return MockAIClient()

    if _ai_client is None:
        if not GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not set, using mock client")
            _ai_client = MockAIClient()
        else:
            _ai_client = GeminiClient()

    return _ai_client
