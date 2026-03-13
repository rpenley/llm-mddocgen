import json

from llm_mddocgen.synthesis.runner import OpenAICompatibleModelClient


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def read(self) -> bytes:
        return json.dumps({"choices": [{"message": {"content": "# Overview\n\nok"}}]}).encode("utf-8")


def test_openai_client_includes_thinking_toggle(monkeypatch) -> None:
    captured: dict = {}

    def _fake_urlopen(request, timeout=0):  # type: ignore[no-untyped-def]
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    client = OpenAICompatibleModelClient(
        base_url="http://localhost:5000/v1",
        model="model",
        thinking_output=False,
    )
    client.complete("system", "user")

    assert captured["body"]["chat_template_kwargs"]["enable_thinking"] is False
