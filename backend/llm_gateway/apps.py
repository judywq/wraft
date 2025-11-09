from django.apps import AppConfig


class LlmCallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.llm_gateway"
    verbose_name = "LLM Gateway"

    def ready(self) -> None:
        # Import signals to register them
        import backend.llm_gateway.signals  # noqa: F401
