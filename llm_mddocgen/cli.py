import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from .artifacts import _append_root_log, _collect_tags, _write_internal_manifest, _write_task_artifacts
from .config import PACKAGE_DEFAULTS, load_config
from .loader import _load_persona_definition, _load_project_definition, _load_task_definition, _load_template_definition
from .models import GlobalConfig, PersonaDefinition, ProjectDefinition, RunSummary, SourceDocument, TaskDefinition, TaskRunArtifacts
from .report import _generate_report
from .retrieval.websearch import gather_web_sources
from .scanner import discover_personas, discover_tasks, discover_templates, filter_tasks
from .synthesis.runner import build_model_client

VERSION = "0.1.0"


def _utc_now() -> datetime:
	return datetime.now(UTC).replace(microsecond=0)


def _compact_timestamp(now: datetime) -> str:
	return now.strftime("%Y%m%dT%H%M%S")


def _col(value: str, width: int) -> str:
	return value.ljust(width)


def process_task(task_path: Path, config: GlobalConfig, timestamp: str, project_file: Path | None = None) -> TaskRunArtifacts:
	task = _load_task_definition(task_path)
	label = task.name

	template_definition = _load_template_definition(config.templates_root, config.builtin_templates_root, task.task_template)
	task.template_definition = template_definition

	if project_file is not None:
		# Load project directly from explicit file path
		from .frontmatter import read_markdown_with_frontmatter
		frontmatter, body = read_markdown_with_frontmatter(project_file)
		task.project_definition = ProjectDefinition(
			name=project_file.stem,
			directory=project_file.parent,
			project_file=project_file,
			body=body,
			frontmatter=frontmatter,
		)
		task.project_name = task.project_name or project_file.stem
	elif task.project_name:
		project_definition = _load_project_definition(config.projects_root, task.project_name)
		task.project_definition = project_definition
		if project_definition is None:
			print(f"[{label}] warning: project '{task.project_name}' not found, continuing without project context", file=sys.stderr)

	project_label = f"  project={task.project_name}" if task.project_name else ""
	print(f"[{label}] persona={task.persona_name}  template={task.task_template}{project_label}")

	persona = _load_persona_definition(config.personas_root, config.builtin_personas_root, task.persona_name)
	sources = _collect_sources_with_progress(task, persona, config, task.name)

	if config.llm.web_search:
		model_client = build_model_client(config)
		web_sources = gather_web_sources(model_client, task, config)
		if web_sources:
			print(f"[{label}] web sources: {len(web_sources)} pages")
			sources = sources + web_sources

	model_hint = config.llm.model if config.llm.enabled else "fallback"
	print(f"[{label}] generating report ({model_hint})...")

	report_markdown, model_label, thinking = _generate_report(task, persona, sources, config)
	tags = _collect_tags(
		task.frontmatter,
		persona.frontmatter,
		task.template_definition.frontmatter if task.template_definition else {},
		task.project_definition.frontmatter if task.project_definition else {},
	)
	artifacts = _write_task_artifacts(task, timestamp, report_markdown, sources, model_label, config, thinking, tags=tags)
	_write_internal_manifest(task, persona, artifacts, config)

	try:
		report_rel = artifacts.report_file.relative_to(Path.cwd())
	except ValueError:
		report_rel = artifacts.report_file
	print(f"[{label}] done → {report_rel}")

	return artifacts


def _collect_sources_with_progress(task: TaskDefinition, persona: PersonaDefinition, config: GlobalConfig, task_name: str) -> list[SourceDocument]:
	from .sources import _collect_sources
	sources = _collect_sources(task, persona, config)
	print(f"[{task_name}] sources: {len(sources)} files")
	return sources


def _cmd_list_personas(config: GlobalConfig) -> int:
	persona_dirs = discover_personas(config.personas_root, config.builtin_personas_root)
	if not persona_dirs:
		print("no personas found")
		return 0
	name_width = max(len(d.stem) for d in persona_dirs)
	print(f"personas ({len(persona_dirs)}):")
	for persona_dir in persona_dirs:
		persona = _load_persona_definition(config.personas_root, config.builtin_personas_root, persona_dir.stem)
		description = persona.frontmatter.get("description", persona.frontmatter.get("tone", ""))
		print(f"  {_col(persona_dir.stem, name_width)}  {description}")
	return 0


def _cmd_list_tasks(tasks_root: Path) -> int:
	task_dirs = discover_tasks(tasks_root)
	if not task_dirs:
		print("no tasks found")
		return 0
	print(f"tasks ({len(task_dirs)}):")
	for task_dir in task_dirs:
		task = _load_task_definition(task_dir)
		print(f"  {task.name}  persona={task.persona_name}  template={task.task_template}")
	return 0


def _cmd_list_templates(config: GlobalConfig) -> int:
	template_files = discover_templates(config.templates_root, config.builtin_templates_root)
	if not template_files:
		print("no templates found")
		return 0
	name_width = max(len(p.stem) for p in template_files)
	print(f"templates ({len(template_files)}):")
	for template_file in template_files:
		template_def = _load_template_definition(config.templates_root, config.builtin_templates_root, template_file.stem)
		description = template_def.frontmatter.get("description", template_def.frontmatter.get("objective", "")) if template_def else ""
		print(f"  {_col(template_file.stem, name_width)}  {description}")
	return 0


def _cmd_init_task(path: Path) -> int:
	path = path.resolve()
	if path.exists():
		print(f"error: {path} already exists", file=sys.stderr)
		return 1
	path.parent.mkdir(parents=True, exist_ok=True)
	shutil.copy(PACKAGE_DEFAULTS / "example-task.md", path)
	print(f"wrote starter task to {path}")
	return 0


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(
		description="llm-mddocgen - Large Language Model Markdown Document Generator",
		epilog="Environment: LLM_MDDOCGEN_API_KEY sets the LLM API key. Config: llm-mddocgen.toml in the current directory if present, otherwise ~/.llm-mddocgen/config.toml.",
	)

	parser.add_argument(
		"task_files",
		nargs="*",
		type=Path,
		metavar="TASK_FILE",
		help="task.md file(s) to run",
	)

	task_group = parser.add_argument_group("task execution")
	task_group.add_argument("--task", type=Path, default=None, metavar="PATH", help="Task markdown file to run")
	task_group.add_argument("--project", type=Path, default=None, metavar="PATH", help="Project markdown file to associate with --task")
	task_group.add_argument("--tasks-dir", type=Path, default=None, metavar="PATH", help="Run all tasks found in a directory (default: ./tasks/ if present)")
	task_group.add_argument("--project-dir", type=Path, default=None, metavar="PATH", help="Directory containing project markdown files (default: ./projects/ if present)")
	task_group.add_argument("--fail-fast", action="store_true", help="Stop on first task failure")

	profile_group = parser.add_argument_group("profile")
	profile_group.add_argument(
		"--profile",
		default=None,
		metavar="NAME",
		help="Profile name to load from <profile-root>/<name>/ (injected into every prompt)",
	)
	profile_group.add_argument(
		"--profile-path",
		type=Path,
		default=None,
		dest="profile_location",
		metavar="PATH",
		help="Override the profile root directory",
	)

	output_group = parser.add_argument_group("output paths")
	output_group.add_argument(
		"--output-path",
		type=Path,
		default=None,
		dest="generated_location",
		metavar="PATH",
		help="Override the output directory (default: ./output/)",
	)

	config_group = parser.add_argument_group("configuration")
	config_group.add_argument(
		"--config",
		type=Path,
		default=None,
		metavar="PATH",
		help="Project TOML config file (default: ./llm-mddocgen.toml; if present, used exclusively — otherwise ~/.llm-mddocgen/config.toml is used)",
	)

	action_group = parser.add_argument_group("actions")
	action_group.add_argument("--version", action="store_true", help="Print version and exit")
	action_group.add_argument("--init-task", type=Path, default=None, metavar="PATH", help="Write a starter task.md to PATH and exit")
	action_group.add_argument("--list", choices=["personas", "tasks", "templates"], metavar="{personas,tasks,templates}", default=None, help="List personas, tasks, or templates and exit")
	action_group.add_argument("--dry-run", action="store_true", help="Show what would run without executing")

	args = parser.parse_args(argv)

	if args.version:
		print(f"llm-mddocgen {VERSION}")
		return 0

	if args.init_task:
		return _cmd_init_task(args.init_task)

	config = load_config(
		config_path=args.config,
		generated_root=args.generated_location,
		profile_name=args.profile,
	)

	if args.profile_location is not None:
		profile_location = args.profile_location if args.profile_location.is_absolute() else (Path.cwd() / args.profile_location).resolve()
		config.profile_root = profile_location

	# Apply --project-dir override, or auto-discover ./projects/
	if args.project_dir is not None:
		config.projects_root = args.project_dir.resolve()
	elif config.projects_root is None:
		auto_projects = Path.cwd() / "projects"
		if auto_projects.is_dir():
			config.projects_root = auto_projects
		else:
			print("note: no projects directory found (looked for ./projects/); use --project-dir to set one")

	# Resolve tasks directory: --tasks-dir flag, else auto-discover ./tasks/
	tasks_dir: Path | None = None
	if args.tasks_dir is not None:
		tasks_dir = args.tasks_dir
	else:
		auto_tasks = Path.cwd() / "tasks"
		if auto_tasks.is_dir():
			tasks_dir = auto_tasks

	if args.list == "personas":
		return _cmd_list_personas(config)
	if args.list == "templates":
		return _cmd_list_templates(config)
	if args.list == "tasks":
		if not tasks_dir:
			print("error: no tasks directory found; use --tasks-dir to specify one", file=sys.stderr)
			return 2
		return _cmd_list_tasks(tasks_dir)

	# Validate --project without --task
	if args.project and not args.task:
		print("error: --project requires --task", file=sys.stderr)
		return 2

	# Resolve task paths from all sources
	task_paths: list[tuple[Path, Path | None]] = []  # (task_path, project_file)

	if args.task:
		task_path = args.task.resolve()
		if not task_path.exists():
			print(f"error: {task_path} does not exist", file=sys.stderr)
			return 2
		project_file = args.project.resolve() if args.project else None
		if project_file and not project_file.exists():
			print(f"error: project file {project_file} does not exist", file=sys.stderr)
			return 2
		task_paths.append((task_path, project_file))
	elif args.task_files:
		for task_file in args.task_files:
			task_file = task_file.resolve()
			if not task_file.exists():
				print(f"error: {task_file} does not exist", file=sys.stderr)
				return 2
			task_paths.append((task_file, None))
	elif tasks_dir:
		discovered = discover_tasks(tasks_dir)
		for task_dir in discovered:
			task_paths.append((task_dir, None))
	else:
		print("error: no tasks found — specify --task PATH, pass task files directly, or place tasks in ./tasks/", file=sys.stderr)
		if not (Path.cwd() / "tasks").is_dir():
			print("hint: create a tasks/ directory in the current folder or use --tasks-dir", file=sys.stderr)
		return 2

	if args.dry_run:
		if not task_paths:
			print("no tasks found")
			return 0
		print(f"dry run ({len(task_paths)} tasks):")
		for task_path, project_file in task_paths:
			task = _load_task_definition(task_path)
			project_note = f"  project-file={project_file}" if project_file else (f"  project={task.project_name}" if task.project_name else "")
			status = "  [disabled]" if not task.enabled else ""
			print(f"  {task.name}  persona={task.persona_name}  template={task.task_template}{project_note}{status}")
		return 0

	if not task_paths:
		print("no tasks found")
		return 0

	run_timestamp = _compact_timestamp(_utc_now())
	failures = 0
	summaries: list[RunSummary] = []

	for task_path, project_file in task_paths:
		task_label = task_path.stem if task_path.is_file() else task_path.name
		try:
			# Peek at enabled flag before full processing
			_peek = _load_task_definition(task_path)
			if not _peek.enabled:
				print(f"[{_peek.name}] skipped (enabled: false)")
				summaries.append(RunSummary(run_timestamp=run_timestamp, task_name=_peek.name, status="skipped"))
				continue
			artifacts = process_task(task_path, config=config, timestamp=run_timestamp, project_file=project_file)
			notes = [
				f"report: {artifacts.report_file}",
				f"sources: {len(artifacts.all_sources)} files",
			]
			if artifacts.thinking_file:
				notes.append(f"thinking: {artifacts.thinking_file}")
			summaries.append(
				RunSummary(
					run_timestamp=run_timestamp,
					task_name=artifacts.task_name,
					status="success",
					notes=notes,
				)
			)
		except Exception as exc:
			failures += 1
			message = str(exc)
			summaries.append(
				RunSummary(
					run_timestamp=run_timestamp,
					task_name=task_label,
					status="failed",
					notes=[message],
				)
			)
			print(f"[{task_label}] failed: {message}", file=sys.stderr)
			if args.fail_fast:
				_append_root_log(config, run_timestamp, summaries)
				return 1

	_append_root_log(config, run_timestamp, summaries)
	return 1 if failures else 0
