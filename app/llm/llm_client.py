"""Cliente HTTP explícito: Python → Ollama → LLM."""
from dataclasses import dataclass
import os

import httpx


class LLMError(RuntimeError):
    """Falha acionável na comunicação com o modelo."""


@dataclass(frozen=True)
class Settings:
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    timeout: float = 180
    temperature: float = 0.2
    num_ctx: int = 4096
    num_predict: int = 512
    system_prompt: str = (
        "Você é um assistente técnico. Responda em português com clareza e concisão. "
        "Declare incertezas e não invente fontes. "
        "Você ainda não tem acesso a documentos ou ferramentas."
    )

    def __post_init__(self):
        if not 0 <= self.temperature <= 2:
            raise ValueError("TEMPERATURE deve estar entre 0 e 2.")
        if not 0 < self.timeout < float("inf"):
            raise ValueError("OLLAMA_TIMEOUT deve ser positivo e finito.")
        if self.num_ctx < 512 or not 0 < self.num_predict < self.num_ctx:
            raise ValueError("NUM_CTX >= 512 e 0 < NUM_PREDICT < NUM_CTX são necessários.")

    @classmethod
    def from_env(cls):
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", cls.base_url),
            model=os.getenv("OLLAMA_MODEL", cls.model),
            timeout=float(os.getenv("OLLAMA_TIMEOUT", cls.timeout)),
            temperature=float(os.getenv("TEMPERATURE", cls.temperature)),
            num_ctx=int(os.getenv("NUM_CTX", cls.num_ctx)),
            num_predict=int(os.getenv("NUM_PREDICT", cls.num_predict)),
            system_prompt=os.getenv("SYSTEM_PROMPT", cls.system_prompt),
        )


@dataclass(frozen=True)
class Reply:
    text: str
    prompt_tokens: int
    output_tokens: int
    seconds: float
    truncated: bool


class LLMClient:
    def __init__(self, settings: Settings, http: httpx.Client):
        self.settings = settings
        self.http = http

    def chat(self, messages: list[dict[str, str]]) -> Reply:
        settings = self.settings
        try:
            response = self.http.post(
                settings.base_url.rstrip("/") + "/api/chat",
                json={
                    "model": settings.model,
                    "messages": messages,
                    "stream": False,
                    "keep_alive": "2m",
                    "options": {
                        "temperature": settings.temperature,
                        "num_ctx": settings.num_ctx,
                        "num_predict": settings.num_predict,
                    },
                },
                timeout=settings.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMError("Tempo esgotado. Tente novamente ou aumente OLLAMA_TIMEOUT.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise LLMError(
                    f"Modelo ou endpoint não encontrado. Confira a URL e execute: ollama pull {settings.model}"
                ) from exc
            raise LLMError(f"Ollama retornou HTTP {exc.response.status_code}. Confira o servidor.") from exc
        except httpx.RequestError as exc:
            raise LLMError("Não foi possível acessar Ollama. Execute: ollama serve") from exc
        try:
            data = response.json()
            content = data["message"]["content"]
            if not isinstance(content, str) or not content.strip() or data.get("done") is not True:
                raise ValueError("Resposta vazia ou incompleta.")
            return Reply(
                text=content,
                prompt_tokens=int(data.get("prompt_eval_count", 0)),
                output_tokens=int(data.get("eval_count", 0)),
                seconds=float(data.get("total_duration", 0)) / 1e9,
                truncated=data.get("done_reason") == "length",
            )
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise LLMError("Ollama retornou uma resposta inválida ou vazia.") from exc


class Conversation:
    """Histórico em memória; falhas não adicionam mensagens à conversa."""
    def __init__(self, client: LLMClient):
        self.client = client
        self.clear()

    def clear(self):
        self.messages = [{"role": "system", "content": self.client.settings.system_prompt}]

    def ask(self, question: str) -> Reply:
        if not question.strip():
            raise ValueError("A pergunta não pode estar vazia.")
        # Mantém no máximo quatro turnos anteriores; não é contagem de tokens.
        messages = [self.messages[0], *self.messages[1:][-8:],
                    {"role": "user", "content": question}]
        reply = self.client.chat(messages)
        self.messages = [*messages, {"role": "assistant", "content": reply.text}]
        return reply
