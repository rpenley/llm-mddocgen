"""LLM model client implementations for llm-mddocgen synthesis."""

from dataclasses import dataclass
import json
import re
import urllib.error
import urllib.request
from typing import Protocol

from ..models import GlobalConfig

_THINK_TAG = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)
_THINK_CLOSE = re.compile(r"</think>", re.IGNORECASE)


def _extract_thinking(content: str) -> tuple[str, str]:
	# Standard case: properly wrapped <think>...</think> blocks.
	if _THINK_TAG.search(content):
		thinking_blocks = _THINK_TAG.findall(content)
		thinking = "\n\n".join(block.strip() for block in thinking_blocks if block.strip())
		clean = _THINK_TAG.sub("", content).strip()
		return clean, thinking

	# Orphan </think>: model emitted thinking without an opening tag, then closed with </think>.
	if _THINK_CLOSE.search(content):
		parts = _THINK_CLOSE.split(content, maxsplit=1)
		thinking = parts[0].strip()
		clean = parts[1].strip() if len(parts) > 1 else ""
		return clean, thinking

	return content.strip(), ""


class ModelClient(Protocol):
	def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, str]: ...
	def label(self) -> str: ...


@dataclass
class StubModelClient:
	def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
		return "[MVP stubbed model output]", ""

	def label(self) -> str:
		return "stub"


@dataclass
class OpenAICompatibleModelClient:
	base_url: str
	model: str
	thinking_output: bool = False
	api_key: str = ""
	timeout_seconds: int = 60
	temperature: float = 0.2
	max_tokens: int = 1200

	def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
		endpoint = self.base_url.rstrip("/") + "/chat/completions"

		payload = {
			"model": self.model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			"temperature": self.temperature,
			"max_tokens": self.max_tokens,
			# Non-standard field; ignored by standard OpenAI endpoints, required for vLLM/Ollama thinking mode.
			"chat_template_kwargs": {"enable_thinking": self.thinking_output},
		}
		data = json.dumps(payload).encode("utf-8")
		headers = {"Content-Type": "application/json"}
		if self.api_key:
			headers["Authorization"] = f"Bearer {self.api_key}"

		request = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
		try:
			with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
				raw = response.read().decode("utf-8")
		except urllib.error.HTTPError as exc:
			detail = exc.read().decode("utf-8", errors="replace")
			raise RuntimeError(f"llm HTTP {exc.code} from {endpoint}: {detail[:400]}") from exc
		except urllib.error.URLError as exc:
			raise RuntimeError(f"llm connection failed for {endpoint}: {exc.reason}") from exc

		decoded = json.loads(raw)
		choices = decoded.get("choices") or []
		if not choices:
			raise RuntimeError("llm returned no choices")

		content = choices[0].get("message", {}).get("content", "")
		if not isinstance(content, str) or not content.strip():
			raise RuntimeError("llm returned empty content")

		clean, thinking = _extract_thinking(content)
		return clean, thinking

	def request_search_queries(self, task_body: str, max_queries: int) -> list[str]:
		"""Ask the model to generate web search queries via tool use.

		Returns a list of query strings, or [] if the API does not support
		tool use or the model chooses not to call the tool.  All errors are
		caught so this never breaks the pipeline.
		"""
		tools = [
			{
				"type": "function",
				"function": {
					"name": "web_search",
					"description": "Search the web for current information relevant to the task.",
					"parameters": {
						"type": "object",
						"properties": {
							"query": {
								"type": "string",
								"description": "The search query to execute.",
							}
						},
						"required": ["query"],
					},
				},
			}
		]
		payload = {
			"model": self.model,
			"messages": [
				{
					"role": "system",
					"content": (
						f"You are a research assistant. Use the web_search tool to look up "
						f"information relevant to the task below. Make at most {max_queries} "
						"targeted searches. Only search for things that would materially "
						"improve the output. If you have enough context already, do not search."
					),
				},
				{"role": "user", "content": task_body[:2000]},
			],
			"tools": tools,
			"temperature": self.temperature,
			"max_tokens": self.max_tokens,
		}
		data = json.dumps(payload).encode("utf-8")
		headers = {"Content-Type": "application/json"}
		if self.api_key:
			headers["Authorization"] = f"Bearer {self.api_key}"
		endpoint = self.base_url.rstrip("/") + "/chat/completions"
		request = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
		try:
			with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
				decoded = json.loads(response.read().decode("utf-8"))
		except Exception:
			return []

		choices = decoded.get("choices") or []
		if not choices:
			return []
		message = choices[0].get("message") or {}
		tool_calls = message.get("tool_calls") or []
		queries: list[str] = []
		for call in tool_calls:
			if not isinstance(call, dict):
				continue
			function = call.get("function") or {}
			if function.get("name") != "web_search":
				continue
			try:
				args = json.loads(function.get("arguments", "{}"))
				query = str(args.get("query", "")).strip()
				if query:
					queries.append(query)
			except Exception:
				continue
		return queries[:max_queries]

	def label(self) -> str:
		return f"openai-compatible:{self.model}@{self.base_url}"


def build_model_client(config: GlobalConfig) -> ModelClient | None:
	if not config.llm.enabled:
		return None
	return OpenAICompatibleModelClient(
		base_url=config.llm.base_url,
		model=config.llm.model,
		thinking_output=config.llm.thinking_output,
		api_key=config.llm.api_key,
		timeout_seconds=config.llm.timeout_seconds,
		temperature=config.llm.temperature,
		max_tokens=config.llm.max_tokens,
	)
