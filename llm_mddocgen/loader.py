"""Loads task, persona, and template definitions from disk.
All functions here are read-only: they take paths and return dataclasses with no side effects."""

from pathlib import Path

from .constants import DATA_DIR, PERSONA_FILE, PROJECT_FILE, TASK_FILE
from .frontmatter import read_markdown_with_frontmatter
from .models import PersonaDefinition, ProjectDefinition, TaskDefinition, TaskTemplateDefinition


def _read_definition(path: Path) -> tuple[dict, str]:
	if not path.exists():
		raise FileNotFoundError(f"required file missing: {path}")
	return read_markdown_with_frontmatter(path)


def _load_task_definition(task_path: Path) -> TaskDefinition:
	if task_path.is_dir():
		task_file = task_path / TASK_FILE
		task_dir = task_path
	elif task_path.name == TASK_FILE:
		task_file = task_path
		task_dir = task_path.parent
	else:
		task_file = task_path
		task_dir = task_path.parent / task_path.stem
	frontmatter, body = _read_definition(task_file)
	task_name = str(frontmatter.get("name", "")).strip()
	persona_name = str(frontmatter.get("persona", "")).strip()
	task_template = str(frontmatter.get("template", "")).strip()
	project_name = str(frontmatter.get("project", "")).strip()
	enabled = bool(frontmatter.get("enabled", True))
	errors: list[str] = []
	if not task_name:
		errors.append("missing required frontmatter field: 'name'")
	if not persona_name:
		errors.append("missing required frontmatter field: 'persona'")
	if not task_template:
		errors.append("missing required frontmatter field: 'template'")
	if errors:
		raise ValueError(f"{task_file}: " + "; ".join(errors))
	return TaskDefinition(
		name=task_name,
		directory=task_dir,
		task_file=task_file,
		persona_name=persona_name,
		frontmatter=frontmatter,
		body=body,
		task_template=task_template,
		project_name=project_name,
		enabled=enabled,
	)


def _load_template_definition(user_root: Path | None, builtin_root: Path, template_name: str) -> TaskTemplateDefinition | None:
	if not template_name:
		return None
	# Check user root first, then builtin
	for root in [user_root, builtin_root]:
		if root is None:
			continue
		template_file = root / f"{template_name}.md"
		if template_file.exists():
			frontmatter, body = read_markdown_with_frontmatter(template_file)
			return TaskTemplateDefinition(
				name=str(frontmatter.get("name", template_name)),
				body=body,
				frontmatter=frontmatter,
			)
	return None


def _load_project_definition(projects_root: Path | None, project_name: str) -> ProjectDefinition | None:
	if not project_name or projects_root is None:
		return None
	# Support both directory-style (<root>/<name>/project.md) and flat file (<root>/<name>.md)
	directory_style = projects_root / project_name
	flat_style = projects_root / f"{project_name}.md"
	if directory_style.is_dir() and (directory_style / PROJECT_FILE).exists():
		project_file = directory_style / PROJECT_FILE
		directory = directory_style
	elif flat_style.exists():
		project_file = flat_style
		directory = projects_root
	else:
		return None
	frontmatter, body = read_markdown_with_frontmatter(project_file)
	return ProjectDefinition(
		name=project_name,
		directory=directory,
		project_file=project_file,
		body=body,
		frontmatter=frontmatter,
	)


def _load_persona_definition(user_root: Path | None, builtin_root: Path, persona_name: str) -> PersonaDefinition:
	# Check user root first, then builtin; support both flat <name>.md and directory <name>/persona.md
	for root in [user_root, builtin_root]:
		if root is None:
			continue
		flat_file = root / f"{persona_name}.md"
		if flat_file.exists():
			frontmatter, body = _read_definition(flat_file)
			return PersonaDefinition(
				name=persona_name,
				directory=root,
				persona_file=flat_file,
				data_dir=root / persona_name / DATA_DIR,
				frontmatter=frontmatter,
				body=body,
			)
		directory = root / persona_name
		persona_file = directory / PERSONA_FILE
		if persona_file.exists():
			frontmatter, body = _read_definition(persona_file)
			return PersonaDefinition(
				name=persona_name,
				directory=directory,
				persona_file=persona_file,
				data_dir=directory / DATA_DIR,
				frontmatter=frontmatter,
				body=body,
			)
	raise FileNotFoundError(
		f"assigned persona '{persona_name}' cannot be resolved: "
		f"not found in user root ({user_root}) or builtin root ({builtin_root})"
	)
