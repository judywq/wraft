from django.dispatch import Signal

# Signal that will be sent when an LLM request is completed
llm_request_completed = Signal()
