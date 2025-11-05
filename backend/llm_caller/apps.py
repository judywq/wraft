from django.apps import AppConfig


class LlmCallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.llm_caller"
    verbose_name = "LLM"

    def ready(self) -> None:
        import backend.llm_caller.signals  # noqa: F401
