"""Plain-text web fetching and DuckDuckGo search for source gathering."""

import html.parser
import sys
import urllib.error
import urllib.parse
import urllib.request


_USER_AGENT = "Mozilla/5.0 (compatible; llm-mddocgen/0.1; +https://github.com/llm-mddocgen)"


class _DDGLinkExtractor(html.parser.HTMLParser):
	"""Extracts result URLs from DuckDuckGo HTML lite search results."""

	def __init__(self) -> None:
		super().__init__()
		self.urls: list[str] = []
		self._capture_next = False

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		if tag != "a":
			return
		attrs_dict = dict(attrs)
		href = attrs_dict.get("href") or ""
		css = attrs_dict.get("class") or ""
		if "result__a" not in css:
			return
		# DDG lite hrefs look like: /l/?uddg=https%3A%2F%2Fexample.com%2F&kh=-1&rut=...
		if "uddg=" in href:
			parsed = urllib.parse.urlparse(href)
			params = urllib.parse.parse_qs(parsed.query)
			if "uddg" in params:
				self.urls.append(urllib.parse.unquote(params["uddg"][0]))
		elif href.startswith("http"):
			self.urls.append(href)


class _TextExtractor(html.parser.HTMLParser):
	"""Strips HTML tags and returns visible text, skipping script/style/nav."""

	_SKIP_TAGS = frozenset({"script", "style", "head", "nav", "footer", "header", "noscript", "meta", "link"})

	def __init__(self) -> None:
		super().__init__()
		self._skip_depth = 0
		self.parts: list[str] = []

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		if tag.lower() in self._SKIP_TAGS:
			self._skip_depth += 1

	def handle_endtag(self, tag: str) -> None:
		if tag.lower() in self._SKIP_TAGS:
			self._skip_depth = max(0, self._skip_depth - 1)

	def handle_data(self, data: str) -> None:
		if self._skip_depth == 0:
			stripped = data.strip()
			if stripped:
				self.parts.append(stripped)

	def get_text(self) -> str:
		return " ".join(self.parts)


def search(query: str, max_results: int = 5, timeout: int = 15) -> list[str]:
	"""Search DuckDuckGo and return up to max_results result URLs."""
	encoded = urllib.parse.urlencode({"q": query})
	url = f"https://html.duckduckgo.com/html/?{encoded}"
	request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
	try:
		with urllib.request.urlopen(request, timeout=timeout) as response:
			raw_html = response.read().decode("utf-8", errors="replace")
	except Exception as exc:
		print(f"warning: DuckDuckGo search failed for {query!r}: {exc}", file=sys.stderr)
		return []

	parser = _DDGLinkExtractor()
	try:
		parser.feed(raw_html)
	except Exception as exc:
		print(f"warning: failed to parse DuckDuckGo results: {exc}", file=sys.stderr)
	return parser.urls[:max_results]


def fetch_text(url: str, timeout: int = 15, max_chars: int = 4000) -> str:
	"""Fetch a URL and return its content as plain text."""
	request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
	try:
		with urllib.request.urlopen(request, timeout=timeout) as response:
			content_type = response.info().get_content_type() or ""
			charset = response.info().get_content_charset("utf-8")
			raw = response.read()
	except urllib.error.HTTPError as exc:
		return f"[HTTP {exc.code} fetching {url}]"
	except Exception as exc:
		return f"[Failed to fetch {url}: {exc}]"

	if "html" not in content_type:
		# Plain text, XML, JSON, etc.
		try:
			return raw.decode(charset, errors="replace")[:max_chars]
		except Exception:
			return raw.decode("utf-8", errors="replace")[:max_chars]

	extractor = _TextExtractor()
	try:
		extractor.feed(raw.decode(charset, errors="replace"))
		text = extractor.get_text()
	except Exception:
		text = raw.decode("utf-8", errors="replace")

	return text[:max_chars]
