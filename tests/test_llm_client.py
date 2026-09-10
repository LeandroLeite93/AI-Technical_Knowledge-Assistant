import httpx
import pytest

from app.llm.llm_client import Conversation, LLMClient, LLMError, Settings


def test_conversation_preserves_context_and_clear():
    requests = []

    def handler(request):
        import json
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "message": {"content": "Uma unidade de dados."}, "done": True,
            "prompt_eval_count": 30, "eval_count": 8, "total_duration": 1000000000,
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        conversation = Conversation(LLMClient(Settings(), http))
        reply = conversation.ask("O que é uma APDU?")
        conversation.ask("Resuma.")
        assert requests[1]["messages"][-2]["role"] == "assistant"
        assert requests[1]["messages"][-3]["content"] == "O que é uma APDU?"
        assert reply.seconds == 1
        assert reply.output_tokens == 8
        conversation.clear()
        assert len(conversation.messages) == 1
        assert conversation.messages[0]["role"] == "system"


@pytest.mark.parametrize("failure", ["timeout", "connection", "missing", "invalid", "empty"])
def test_failure_does_not_modify_history(failure):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        if failure == "connection":
            raise httpx.ConnectError("offline", request=request)
        if failure == "missing":
            return httpx.Response(404)
        if failure == "invalid":
            return httpx.Response(200, text="not json")
        return httpx.Response(200, json={"message": {"content": ""}, "done": True})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        conversation = Conversation(LLMClient(Settings(), http))
        with pytest.raises(LLMError):
            conversation.ask("Teste")
        assert len(conversation.messages) == 1


def test_history_is_bounded_and_keeps_system():
    def handler(request):
        return httpx.Response(200, json={"message": {"content": "ok"}, "done": True})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        conversation = Conversation(LLMClient(Settings(), http))
        for index in range(12):
            conversation.ask(str(index))
        assert len(conversation.messages) == 11
        assert conversation.messages[0]["role"] == "system"
        assert conversation.messages[1]["content"] == "7"


@pytest.mark.parametrize("kwargs", [
    {"temperature": -1}, {"temperature": float("nan")},
    {"timeout": 0}, {"num_ctx": 100}, {"num_predict": 4096},
])
def test_invalid_settings(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)
