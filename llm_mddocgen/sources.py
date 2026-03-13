"""Collects source documents from disk for a given task run.
Sources are grouped by scope: task, persona, profile, generated."""

import sys
from pathlib import Path

from .constants import DATA_DIR, PDF_EXTENSION, SOURCE_EXTENSIONS, SOURCE_EXTENSIONS_WITH_PDF
from .models import GlobalConfig, PersonaDefinition, ProjectDefinition, SourceDocument, TaskDefinition
from .pdf import extract_text as extract_pdf_text


def _iter_text_files(root: Path, include_pdf: bool = False) -> list[Path]:
	if not root.exists() or not root.is_dir():
		return []
	extensions = SOURCE_EXTENSIONS_WITH_PDF if include_pdf else SOURCE_EXTENSIONS
	files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in extensions]
	return sorted(files)


def _read_source(path: Path, scope: str) -> SourceDocument:
	if path.suffix.lower() == PDF_EXTENSION:
		text = extract_pdf_text(path)
	else:
		text = path.read_text(encoding="utf-8")
	return SourceDocument(path=path, scope=scope, text=text)


def _latest_generated_output(generated_dir: Path, task_dir_name: str) -> SourceDocument | None:
	task_generated = generated_dir / task_dir_name
	if not task_generated.exists():
		return None

	candidates = sorted([p for p in task_generated.glob(f"{task_dir_name}-*.md") if p.is_file()])
	if not candidates:
		return None
	latest = candidates[-1]
	return _read_source(latest, "generated")


def _collect_project_sources(project: ProjectDefinition, include_pdf: bool = False) -> list[SourceDocument]:
	sources: list[SourceDocument] = [_read_source(project.project_file, "project")]
	data_dir = project.directory / DATA_DIR
	for path in _iter_text_files(data_dir, include_pdf=include_pdf):
		sources.append(_read_source(path, "project"))
	return sources


def _collect_sources(task: TaskDefinition, persona: PersonaDefinition, config: GlobalConfig) -> list[SourceDocument]:
	pdf = config.allow_pdf_materials
	sources: list[SourceDocument] = [_read_source(task.task_file, "task"), _read_source(persona.persona_file, "persona")]

	for path in _iter_text_files(task.directory, include_pdf=pdf):
		if path == task.task_file:
			continue
		sources.append(_read_source(path, "task"))

	for path in _iter_text_files(persona.data_dir, include_pdf=pdf):
		sources.append(_read_source(path, "persona"))

	if task.project_definition is not None:
		sources.extend(_collect_project_sources(task.project_definition, include_pdf=pdf))

	if config.profile_root is not None:
		if config.profile_name:
			profile_dir = config.profile_root / config.profile_name
			if not profile_dir.exists():
				print(f"[profile] warning: profile '{config.profile_name}' not found at {profile_dir}, skipping", file=sys.stderr)
			else:
				for path in _iter_text_files(profile_dir, include_pdf=pdf):
					sources.append(_read_source(path, "profile"))
		else:
			for path in _iter_text_files(config.profile_root, include_pdf=pdf):
				sources.append(_read_source(path, "profile"))

	latest = _latest_generated_output(config.generated_root, task.name)
	if latest is not None:
		sources.append(latest)

	return sources
