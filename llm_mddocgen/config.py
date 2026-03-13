import os
import sys
from pathlib import Path
from typing import Any

from .models import GlobalConfig, LLMConfig

try:
	import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
	import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_CONFIG_NAME = "llm-mddocgen.toml"
GLOBAL_CONFIG_DIR = Path.home() / ".llm-mddocgen"
GLOBAL_CONFIG_PATH = GLOBAL_CONFIG_DIR / "config.toml"
GLOBAL_DEFAULTS_DIR = GLOBAL_CONFIG_DIR / "default"
GLOBAL_CUSTOM_DIR = GLOBAL_CONFIG_DIR / "custom"
PACKAGE_DEFAULTS = Path(__file__).parent / "defaults"


def _seed_defaults() -> None:
	"""Ensure ~/.llm-mddocgen/ directories exist for user data."""
	GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
	(GLOBAL_CUSTOM_DIR / "personas").mkdir(parents=True, exist_ok=True)
	(GLOBAL_CUSTOM_DIR / "templates").mkdir(parents=True, exist_ok=True)


def _load_toml(path: Path) -> dict[str, Any]:
	if not path.exists():
		return {}
	with path.open("rb") as handle:
		loaded = tomllib.load(handle)
	if not isinstance(loaded, dict):
		print(f"warning: {path} did not parse as a TOML table, ignoring it", file=sys.stderr)
		return {}
	return loaded


def _read_llm_config(data: dict[str, Any]) -> LLMConfig:
	llm_data = data.get("llm", {})
	if not isinstance(llm_data, dict):
		llm_data = {}

	defaults = LLMConfig()
	return LLMConfig(
		enabled=bool(llm_data.get("enabled", defaults.enabled)),
		thinking_output=bool(llm_data.get("thinking_output", defaults.thinking_output)),
		base_url=str(llm_data.get("base_url", defaults.base_url)),
		model=str(llm_data.get("model", defaults.model)),
		api_key=str(llm_data.get("api_key", os.getenv("LLM_MDDOCGEN_API_KEY", defaults.api_key))),
		timeout_seconds=int(llm_data.get("timeout_seconds", defaults.timeout_seconds)),
		temperature=float(llm_data.get("temperature", defaults.temperature)),
		max_tokens=int(llm_data.get("max_tokens", defaults.max_tokens)),
		web_search=bool(llm_data.get("web_search", defaults.web_search)),
		web_search_max_queries=int(llm_data.get("web_search_max_queries", defaults.web_search_max_queries)),
		web_search_max_results=int(llm_data.get("web_search_max_results", defaults.web_search_max_results)),
	)


def _resolve_optional_path(value: str | None, base_dir: Path) -> Path | None:
	if not value:
		return None
	path = Path(value).expanduser()
	if path.is_absolute():
		return path
	return (base_dir / path).resolve()


def load_config(
	config_path: Path | None = None,
	generated_root: Path | None = None,
	profile_name: str | None = None,
) -> GlobalConfig:
	_seed_defaults()

	config_path = config_path or (Path.cwd() / DEFAULT_CONFIG_NAME)
	if config_path.exists():
		data = _load_toml(config_path)
	else:
		data = _load_toml(GLOBAL_CONFIG_PATH)
	base_dir = config_path.parent

	llm = _read_llm_config(data)

	# personas_root and templates_root: config-file override, else ~/.llm-mddocgen/custom/
	personas_root = _resolve_optional_path(data.get("personas_root"), base_dir) or GLOBAL_CUSTOM_DIR / "personas"
	templates_root = _resolve_optional_path(data.get("templates_root"), base_dir) or GLOBAL_CUSTOM_DIR / "templates"

	# profile_root: config-file override, else None (no profile injection)
	profile_root = _resolve_optional_path(data.get("profile_root"), base_dir)

	# projects_root: config-file override, else None (no project loading)
	projects_root = _resolve_optional_path(data.get("projects_root"), base_dir)

	# internal_root: config-file override, else ~/.llm-mddocgen/
	raw_internal = data.get("internal_root")
	if raw_internal:
		internal_path = Path(str(raw_internal)).expanduser()
		internal_root = internal_path if internal_path.is_absolute() else (base_dir / internal_path).resolve()
	else:
		internal_root = GLOBAL_CONFIG_DIR

	# generated_root defaults to CWD-relative; if set in config, resolve relative to config file dir
	raw_generated = data.get("generated_root")
	if generated_root is not None:
		resolved_generated_root = generated_root.resolve()
	elif raw_generated:
		generated_path = Path(str(raw_generated)).expanduser()
		resolved_generated_root = generated_path if generated_path.is_absolute() else (base_dir / generated_path).resolve()
	else:
		resolved_generated_root = (Path.cwd() / "output").resolve()

	raw_global = data.get("global_file")
	if raw_global:
		global_path = Path(str(raw_global)).expanduser()
		global_file = global_path if global_path.is_absolute() else (base_dir / global_path).resolve()
	else:
		global_file = PACKAGE_DEFAULTS / "global.md"

	return GlobalConfig(
		builtin_personas_root=PACKAGE_DEFAULTS / "personas",
		builtin_templates_root=PACKAGE_DEFAULTS / "templates",
		global_file=global_file,
		personas_root=personas_root,
		templates_root=templates_root,
		profile_root=profile_root,
		projects_root=projects_root,
		generated_root=resolved_generated_root,
		internal_root=internal_root,
		profile_name=profile_name,
		allow_pdf_materials=bool(data.get("allow_pdf_materials", False)),
		llm=llm,
	)
