from pathlib import Path

from .constants import MARKDOWN_EXTENSION, PERSONA_FILE, README_STEM, TASK_FILE


def discover_personas(user_root: Path | None, builtin_root: Path) -> list[Path]:
	"""Return persona paths, merging user_root on top of builtin_root.

	Supports both flat <name>.md files and directory <name>/persona.md layouts.
	User personas override builtins on name collision.
	"""
	found: dict[str, Path] = {}

	for root in [builtin_root, user_root]:
		if root is None or not root.exists():
			continue
		for path in root.iterdir():
			if path.is_file() and path.suffix == MARKDOWN_EXTENSION and path.stem.lower() != README_STEM:
				found[path.stem] = path
			elif path.is_dir() and (path / PERSONA_FILE).exists():
				found[path.name] = path

	return sorted(found.values(), key=lambda p: p.stem)


def discover_templates(user_root: Path | None, builtin_root: Path) -> list[Path]:
	"""Return template files, merging user_root on top of builtin_root.

	User templates override builtins on name collision.
	"""
	found: dict[str, Path] = {}

	for root in [builtin_root, user_root]:
		if root is None or not root.exists():
			continue
		for path in root.iterdir():
			if path.is_file() and path.suffix == MARKDOWN_EXTENSION and path.stem.lower() != README_STEM:
				found[path.stem] = path

	return sorted(found.values(), key=lambda p: p.stem)


def _has_frontmatter(path: Path) -> bool:
	try:
		return path.read_text(encoding="utf-8", errors="replace").startswith("---\n")
	except OSError:
		return False


def discover_tasks(tasks_root: Path) -> list[Path]:
	if not tasks_root.exists():
		return []
	if tasks_root.is_file():
		tasks_root = tasks_root.parent
	if (tasks_root / TASK_FILE).exists():
		return [tasks_root]
	results: list[Path] = []
	for path in tasks_root.iterdir():
		if path.is_dir() and (path / TASK_FILE).exists():
			results.append(path)
		elif path.is_file() and path.suffix == MARKDOWN_EXTENSION and path.stem.lower() != README_STEM and _has_frontmatter(path):
			results.append(path)
	return sorted(results, key=lambda p: p.stem)


def filter_tasks(paths: list[Path], selected: list[str] | None) -> list[Path]:
	if not selected:
		return paths
	wanted = set(selected)
	return [p for p in paths if p.name in wanted]
