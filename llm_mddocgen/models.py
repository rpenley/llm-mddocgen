"""Data models for llm-mddocgen: configuration, task definitions, sources, and run artifacts."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class LLMConfig:
	enabled: bool = False
	thinking_output: bool = False
	base_url: str = "http://localhost:11434/v1"
	model: str = "llama3.2"
	api_key: str = ""
	timeout_seconds: int = 60
	temperature: float = 0.2
	max_tokens: int = 1200
	web_search: bool = False
	web_search_max_queries: int = 3
	web_search_max_results: int = 5


@dataclass
class GlobalConfig:
	builtin_personas_root: Path
	builtin_templates_root: Path
	generated_root: Path
	internal_root: Path
	global_file: Path | None = None
	personas_root: Path | None = None
	templates_root: Path | None = None
	tasks_root: Path | None = None
	profile_root: Path | None = None
	profile_name: str | None = None
	projects_root: Path | None = None
	allow_pdf_materials: bool = False
	llm: LLMConfig = field(default_factory=LLMConfig)


@dataclass
class PersonaDefinition:
	name: str
	directory: Path
	persona_file: Path
	data_dir: Path
	frontmatter: dict
	body: str


@dataclass
class TaskTemplateDefinition:
	name: str
	body: str
	frontmatter: dict = field(default_factory=dict)


@dataclass
class TaskDefinition:
	name: str
	directory: Path
	task_file: Path
	persona_name: str
	frontmatter: dict
	body: str
	task_template: str = ""
	template_definition: TaskTemplateDefinition | None = None
	project_name: str = ""
	project_definition: "ProjectDefinition | None" = None
	enabled: bool = True


@dataclass
class ProjectDefinition:
	name: str
	directory: Path
	project_file: Path
	body: str
	frontmatter: dict = field(default_factory=dict)


@dataclass
class SourceDocument:
	path: Path | str
	scope: Literal["task", "persona", "profile", "generated", "project", "web"]
	text: str


@dataclass
class TaskRunArtifacts:
	task_name: str
	timestamp: str
	report_file: Path
	log_file: Path
	all_sources: list[SourceDocument]
	thinking_file: Path | None = None


@dataclass
class RunSummary:
	run_timestamp: str
	task_name: str
	status: Literal["success", "failed", "skipped"]
	persona_name: str | None = None
	notes: list[str] = field(default_factory=list)


