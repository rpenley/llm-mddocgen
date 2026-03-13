"""Web search source gathering: tool-use query generation → DDG search → plain-text fetch."""

import sys

from ..models import GlobalConfig, SourceDocument, TaskDefinition
from ..synthesis.runner import ModelClient, OpenAICompatibleModelClient
from .fetch import fetch_text, search


def gather_web_sources(model_client: ModelClient | None, task: TaskDefinition, config: GlobalConfig) -> list[SourceDocument]:
	"""Return web search results as SourceDocuments.

	Requires:
	  - config.llm.web_search is True
	  - model_client is an OpenAICompatibleModelClient (Ollama or compatible)

	Silently returns [] when web search is disabled, the client type does not
	support tool use, or any network/API error occurs.
	"""
	if not config.llm.web_search:
		return []
	if not isinstance(model_client, OpenAICompatibleModelClient):
		return []

	try:
		queries = model_client.request_search_queries(task.body, config.llm.web_search_max_queries)
	except Exception as exc:
		print(f"[{task.name}] warning: web search query generation failed: {exc}", file=sys.stderr)
		return []

	if not queries:
		return []

	print(f"[{task.name}] web search: {len(queries)} quer{'y' if len(queries) == 1 else 'ies'}")

	sources: list[SourceDocument] = []
	seen_urls: set[str] = set()
	for query in queries:
		urls = search(query, max_results=config.llm.web_search_max_results, timeout=config.llm.timeout_seconds)
		for url in urls:
			if url in seen_urls:
				continue
			seen_urls.add(url)
			text = fetch_text(url, timeout=config.llm.timeout_seconds)
			if text.strip():
				sources.append(SourceDocument(path=url, scope="web", text=f"Source: {url}\n\n{text}"))

	return sources
