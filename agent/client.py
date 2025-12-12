"""
LLM Client
==========

Client for calling LLM APIs with Anthropic-compatible interface.
Supports MiniMax and other providers via base URL override.
"""

import os
from typing import Optional

import anthropic


def create_client() -> anthropic.Anthropic:
    """
    Create an Anthropic client with custom base URL support.
    
    Environment variables:
        ANTHROPIC_API_KEY: API key (required)
        ANTHROPIC_BASE_URL: Custom base URL (optional, for MiniMax etc)
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set.\n"
            "Set it in your .env file or docker-compose.yml"
        )
    
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    
    if base_url:
        print(f"Using custom API endpoint: {base_url}")
        return anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url
        )
    else:
        return anthropic.Anthropic(api_key=api_key)


def get_model() -> str:
    """Get the model name from environment or default."""
    return os.environ.get("ANTHROPIC_MODEL", "MiniMax-M2")


async def call_llm(
    client: anthropic.Anthropic,
    messages: list,
    tools: list,
    system_prompt: Optional[str] = None
) -> anthropic.types.Message:
    """
    Call the LLM with messages and tools.
    
    Args:
        client: Anthropic client
        messages: Conversation messages
        tools: Tool definitions
        system_prompt: Optional system prompt
    
    Returns:
        LLM response message
    """
    from prompts import get_system_prompt
    
    model = get_model()
    system = system_prompt or get_system_prompt()
    
    # Build request
    request_kwargs = {
        "model": model,
        "max_tokens": 8192,
        "system": system,
        "messages": messages,
    }
    
    # Add tools if provided
    if tools:
        request_kwargs["tools"] = tools
    
    # Make the call
    response = client.messages.create(**request_kwargs)
    
    return response
