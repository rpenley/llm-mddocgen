"""PDF text extraction for llm-mddocgen source documents."""

from pathlib import Path


def extract_text(path: Path) -> str:
	"""Extract plain text from a PDF file. Returns an error note if pypdf is not installed."""
	try:
		import pypdf
	except ImportError:
		return f"[PDF text extraction requires pypdf: pip install pypdf]\nFile: {path}\n"

	reader = pypdf.PdfReader(str(path))
	pages: list[str] = []
	for page in reader.pages:
		text = page.extract_text() or ""
		if text.strip():
			pages.append(text)
	if not pages:
		return f"[No extractable text found in {path.name}]\n"
	return "\n\n".join(pages)
