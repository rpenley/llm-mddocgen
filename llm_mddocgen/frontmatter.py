"""Reads and writes markdown files with YAML frontmatter."""

import sys
from pathlib import Path

import yaml


def read_markdown_with_frontmatter(path: Path) -> tuple[dict, str]:
	text = path.read_text(encoding="utf-8")
	if not text.startswith("---\n"):
		return {}, text

	try:
		_, rest = text.split("---\n", 1)
		fm_text, body = rest.split("\n---\n", 1)
	except ValueError:
		print(f"warning: malformed frontmatter delimiters in {path}, ignoring frontmatter", file=sys.stderr)
		return {}, text

	try:
		metadata = yaml.safe_load(fm_text) or {}
	except yaml.YAMLError as exc:
		print(f"warning: could not parse frontmatter YAML in {path}: {exc}", file=sys.stderr)
		return {}, text.split("---\n", 1)[1] if "---\n" in text else text

	if not isinstance(metadata, dict):
		print(f"warning: frontmatter in {path} is not a key/value mapping, ignoring it", file=sys.stderr)
		metadata = {}
	return metadata, body.lstrip("\n")


def write_markdown_with_frontmatter(path: Path, metadata: dict, body: str) -> None:
	fm = yaml.safe_dump(metadata, sort_keys=False).strip()
	content = f"---\n{fm}\n---\n\n{body.strip()}\n"
	path.write_text(content, encoding="utf-8")
