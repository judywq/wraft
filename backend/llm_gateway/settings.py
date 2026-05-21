"""
Configuration settings for the LLM Gateway application.

This module defines configuration constants including LLM purpose choices,
initial model configurations, and API key settings. These settings are
loaded from Django settings or environment variables.
"""

import environ
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

env = environ.Env()

# LLM Purpose Choices
# ------------------------------------------------------------------------------
# Get LLM purpose choices from Django settings
# These define the available use cases for LLM models (e.g., "score", "correction")
LLM_PURPOSE_CHOICES = getattr(settings, "LLM_GATEWAY_LLM_PURPOSE_CHOICES", None)
if not LLM_PURPOSE_CHOICES:
    error_msg = "LLM_GATEWAY_LLM_PURPOSE_CHOICES is not set"
    raise ImproperlyConfigured(error_msg)

# Init LLM Models
# ------------------------------------------------------------------------------
# Initial LLM models to create when the app is initialized
# Each dict contains model configuration: name (API identifier), display_name,
# is_active flag, and order (for UI display)
INIT_LLM_MODELS = [
    {
        "name": "openai/gpt-3.5-turbo",
        "display_name": "GPT-3.5 Turbo",
        "is_active": True,
        "order": 1,
    },
    {
        "name": "openai/ft:gpt-4o-2024-08-06:waseda-university:eassy-eval:AVLSHV8x",
        "display_name": "GPT-4o Finetuned",
        "is_active": True,
        "order": 9,
    },
    {
        "name": "openai/gpt-4o",
        "display_name": "GPT-4o",
        "is_active": True,
        "order": 10,
    },
    {
        "name": "openai/gpt-4o-mini-2024-07-18",
        "display_name": "GPT-4o mini",
        "is_active": True,
        "order": 11,
    },
    {
        "name": "openai/gpt-4.5-preview-2025-02-27",
        "display_name": "GPT-4.5 Preview",
        "is_active": True,
        "order": 12,
    },
    {
        "name": "anthropic/claude-sonnet-4-6",
        "display_name": "Claude Sonnet 4.6",
        "is_active": True,
        "order": 60,
    },
    {
        "name": "anthropic/claude-opus-4-7",
        "display_name": "Claude Opus 4.7",
        "is_active": True,
        "order": 70,
    },
    {
        "name": "anthropic/claude-haiku-4-5-20251001",
        "display_name": "Claude Haiku 4.5",
        "is_active": True,
        "order": 80,
    },
    {
        "name": "groq/llama-3.3-70b-versatile",
        "display_name": "Llama 3.3 70B Versatile 128k",
        "is_active": True,
        "order": 100,
    },
    {
        "name": "groq/deepseek-r1-distill-llama-70b",
        "display_name": "DeepSeek R1 Distill Llama 70B",
        "is_active": True,
        "order": 110,
    },
    {
        "name": "groq/qwen-2.5-32b",
        "display_name": "Qwen 2.5 32B",
        "is_active": True,
        "order": 120,
    },
    {
        "name": "deepseek/deepseek-chat",
        "display_name": "DeepSeek Chat",
        "is_active": True,
        "order": 150,
    },
    {
        "name": "deepseek/deepseek-reasoner",
        "display_name": "DeepSeek Reasoner",
        "is_active": True,
        "order": 160,
    },
]


# Init LLM Configs
# ------------------------------------------------------------------------------
# Initial model configurations to create when the app is initialized
# Loaded from Django settings, defaults to empty dict if not set
INIT_LLM_CONFIGS = getattr(settings, "LLM_GATEWAY_INIT_LLM_CONFIGS", {})

# Init LLM API Keys
# ------------------------------------------------------------------------------
# Initial API keys to create when the app is initialized
# Keys are loaded from environment variables and stored in the database
INIT_LLM_API_KEYS = [
    {
        "env_name": "OPENAI_API_KEY",
        "api_key": env.str("OPENAI_API_KEY", default=""),
        "is_active": True,
    },
    {
        "env_name": "ANTHROPIC_API_KEY",
        "api_key": env.str("ANTHROPIC_API_KEY", default=""),
        "is_active": True,
    },
    {
        "env_name": "GROQ_API_KEY",
        "api_key": env.str("GROQ_API_KEY", default=""),
        "is_active": True,
    },
]
