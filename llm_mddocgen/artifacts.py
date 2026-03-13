"""Writes all output files for a completed task run:
the report markdown, a sources index, a generation log, and the internal manifest."""

import json
from pathlib import Path

from .constants import OUTPUT_LOGS_DIR, OUTPUT_PROJECTS_DIR, OUTPUT_TASKS_DIR
from .models import GlobalConfig, PersonaDefinition, RunSummary, SourceDocument, TaskDefinition, TaskRunArtifacts


def _collect_tags(*frontmatters: dict) -> list[str]:
	seen: set[str] = set()
	result: list[str] = []
	for frontmatter in frontmatters:
		raw = frontmatter.get("tags", [])
		items: list = [raw] if isinstance(raw, str) else (list(raw) if isinstance(raw, list) else [])
		for item in items:
			tag = str(item).strip()
			if tag and tag not in seen:
				seen.add(tag)
				result.append(tag)
	return result


def _write_task_artifacts(task: TaskDefinition, timestamp: str, report_markdown: str, sources: list[SourceDocument], model_label: str, config: GlobalConfig, thinking: str = "", tags: list[str] | None = None) -> TaskRunArtifacts:
	if task.project_name:
		output_dir = config.generated_root / OUTPUT_PROJECTS_DIR / task.project_name
	else:
		output_dir = config.generated_root / OUTPUT_TASKS_DIR
	report_name = f"{task.name}-{timestamp}.md"

	logs_dir = config.generated_root / OUTPUT_LOGS_DIR
	output_dir.mkdir(parents=True, exist_ok=True)
	logs_dir.mkdir(parents=True, exist_ok=True)

	stem = Path(report_name).stem
	report_file = output_dir / report_name
	log_file = logs_dir / f"{stem}.log.md"

	if tags:
		fm_lines = ["---", "tags:"] + [f"  - {tag}" for tag in tags] + ["---", ""]
		report_markdown = "\n".join(fm_lines) + "\n" + report_markdown

	report_file.write_text(report_markdown, encoding="utf-8")

	thinking_file: Path | None = None
	if thinking:
		thinking_file = logs_dir / f"{stem}-thinking.md"
		thinking_lines = [
			f"# Thinking: {task.name}",
			"",
			f"- generated_at: {timestamp}",
			f"- model: {model_label}",
			"",
			thinking,
		]
		thinking_file.write_text("\n".join(thinking_lines) + "\n", encoding="utf-8")

	log_lines = [
		"# Generation Log",
		"",
		f"- task: {task.name}",
		f"- report: {report_file.name}",
		f"- generated_at: {timestamp}",
		f"- model: {model_label}",
		f"- source_count: {len(sources)}",
		"",
		"# Sources",
		"",
	]
	for source in sources:
		log_lines.append(f"- [{source.scope}] {source.path}")
	log_file.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

	return TaskRunArtifacts(
		task_name=task.name,
		timestamp=timestamp,
		report_file=report_file,
		log_file=log_file,
		all_sources=sources,
		thinking_file=thinking_file,
	)


def _write_internal_manifest(task: TaskDefinition, persona: PersonaDefinition, artifacts: TaskRunArtifacts, config: GlobalConfig) -> None:
	manifests_dir = config.internal_root / "manifests"
	state_dir = config.internal_root / "state"

	manifests_dir.mkdir(parents=True, exist_ok=True)
	state_dir.mkdir(parents=True, exist_ok=True)

	manifest = {
		"task": task.name,
		"persona": persona.name,
		"generated_at": artifacts.timestamp,
		"report_file": str(artifacts.report_file),
		"source_files": [str(src.path) for src in artifacts.all_sources],
	}
	(manifests_dir / f"{task.name}-{artifacts.timestamp}.json").write_text(
		json.dumps(manifest, indent=2),
		encoding="utf-8",
	)

	last_run = {
		"task": task.name,
		"persona": persona.name,
		"timestamp": artifacts.timestamp,
		"report_file": str(artifacts.report_file),
	}
	(state_dir / "last_run.json").write_text(json.dumps(last_run, indent=2), encoding="utf-8")


def _append_root_log(config: GlobalConfig, run_timestamp: str, summaries: list[RunSummary]) -> Path:
	logs_dir = config.generated_root / OUTPUT_LOGS_DIR
	logs_dir.mkdir(parents=True, exist_ok=True)
	log_file = logs_dir / f"{run_timestamp}.md"

	lines = ["# llm-mddocgen Run Log", "", f"- run_timestamp: {run_timestamp}", f"- task_count: {len(summaries)}", ""]
	for summary in summaries:
		lines.append(f"## Task {summary.task_name}")
		lines.append(f"- status: {summary.status}")
		if summary.persona_name:
			lines.append(f"- persona: {summary.persona_name}")
		for note in summary.notes:
			lines.append(f"- note: {note}")
		lines.append("")

	log_file.write_text("\n".join(lines), encoding="utf-8")
	return log_file
