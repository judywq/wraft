from django.core.management.base import BaseCommand
from django.db import transaction

from backend.llm_gateway.models import APIKey
from backend.llm_gateway.models import ModelConfig
from backend.llm_gateway.models import LLMModel
from backend.llm_gateway.settings import INIT_LLM_API_KEYS
from backend.llm_gateway.settings import INIT_LLM_CONFIGS
from backend.llm_gateway.settings import INIT_LLM_MODELS
from backend.llm_gateway.helpers import read_prompt_template


class Command(BaseCommand):
    help = "Initialize LLM models and configs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force initialization even if data already exists",
        )

    def init_llm_models(self, force=False):  # noqa: FBT002
        if force:
            LLMModel.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing LLM models"))

        for model in INIT_LLM_MODELS:
            try:
                _, created = LLMModel.objects.get_or_create(**model)
                if created:
                    msg = f"Created LLM model: {model['name']}"
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"LLM model already exists: {model['name']}"
                    self.stdout.write(self.style.WARNING(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create LLM model: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    def init_llm_configs(self, force=False):  # noqa: FBT002
        if force:
            ModelConfig.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing LLM configs"))

        for purpose, config in INIT_LLM_CONFIGS.items():
            try:
                model_name = config["model"]
                model = LLMModel.objects.filter(name=model_name).first()
                if not model:
                    msg = f"Model {model_name} not found"
                    self.stderr.write(self.style.WARNING(msg))

                user_prompt_template = read_prompt_template(config["template"])
                found = ModelConfig.objects.filter(
                    purpose=purpose,
                ).exists()
                if not found:
                    ModelConfig.objects.create(
                        purpose=purpose,
                        user_prompt_template=user_prompt_template,
                        model=model,
                        temperature=config["temperature"],
                        is_active=True,
                    )
                    msg = f"Created LLM config for: {purpose}"
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"LLM config for {purpose} already exists"
                    self.stdout.write(self.style.WARNING(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create config for {purpose}: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    def init_llm_api_keys(self, force=False):  # noqa: FBT002
        if force:
            APIKey.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing API keys"))

        for key_data in INIT_LLM_API_KEYS:
            try:
                _, created = APIKey.objects.get_or_create(
                    name=key_data["env_name"],
                    defaults={
                        "key": key_data["api_key"],
                        "is_active": key_data["is_active"],
                    },
                )
                if created:
                    msg = f"Created API key: {key_data['env_name']}"
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"API key already exists: {key_data['env_name']}"
                    self.stdout.write(self.style.WARNING(msg))
            except (ValueError, TypeError) as e:
                msg = f"Failed to create API key: {e!s}"
                self.stderr.write(self.style.ERROR(msg))

    @transaction.atomic
    def handle(self, *args, **kwargs):
        force = kwargs.get("force", False)

        self.stdout.write("Starting LLM data initialization...")

        try:
            self.init_llm_models(force)
            self.init_llm_configs(force)
            self.init_llm_api_keys(force)
            msg = "Successfully initialized LLM data"
            self.stdout.write(self.style.SUCCESS(msg))
        except (ValueError, TypeError) as e:
            msg = f"Failed to initialize LLM data: {e!s}"
            self.stderr.write(self.style.ERROR(msg))
