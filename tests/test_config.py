from pathlib import Path
from unittest.mock import patch

from llm_mddocgen.config import GLOBAL_CONFIG_DIR, GLOBAL_CUSTOM_DIR, PACKAGE_DEFAULTS, load_config


def _no_seed(func):
	"""Decorator to skip default seeding during tests."""
	from functools import wraps
	@wraps(func)
	def wrapper(*args, **kwargs):
		with patch("llm_mddocgen.config._seed_defaults"):
			return func(*args, **kwargs)
	return wrapper


@_no_seed
def test_load_config_defaults(tmp_path: Path) -> None:
	config = load_config(config_path=tmp_path / "missing.toml")

	assert config.builtin_personas_root == PACKAGE_DEFAULTS / "personas"
	assert config.builtin_templates_root == PACKAGE_DEFAULTS / "templates"
	assert config.builtin_personas_root.exists()
	assert config.builtin_templates_root.exists()
	assert config.personas_root == GLOBAL_CUSTOM_DIR / "personas"
	assert config.templates_root == GLOBAL_CUSTOM_DIR / "templates"
	assert config.profile_root is None
	assert config.internal_root == GLOBAL_CONFIG_DIR
	assert config.generated_root == Path.cwd() / "output"
	assert config.llm.enabled is False


@_no_seed
def test_load_config_custom_roots_and_llm(tmp_path: Path) -> None:
	config_path = tmp_path / "llm_mddocgen.toml"
	config_path.write_text(
		"\n".join(
			[
				'personas_root = "custom-personas"',
				'templates_root = "custom-templates"',
				'profile_root = "custom-profile"',
				'generated_root = "custom-generated"',
				'internal_root = "custom-internal"',
				"",
				"[llm]",
				"enabled = true",
				"thinking_output = true",
				'base_url = "http://localhost:1234/v1"',
				'model = "test-model"',
				'api_key = "secret"',
				"timeout_seconds = 10",
				"temperature = 0.5",
				"max_tokens = 321",
				"",
			]
		),
		encoding="utf-8",
	)

	config = load_config(config_path=config_path)

	assert config.personas_root == tmp_path / "custom-personas"
	assert config.templates_root == tmp_path / "custom-templates"
	assert config.profile_root == tmp_path / "custom-profile"
	assert config.generated_root == tmp_path / "custom-generated"
	assert config.internal_root == tmp_path / "custom-internal"
	assert config.llm.enabled is True
	assert config.llm.thinking_output is True
	assert config.llm.base_url == "http://localhost:1234/v1"
	assert config.llm.model == "test-model"
	assert config.llm.api_key == "secret"
	assert config.llm.timeout_seconds == 10
	assert config.llm.temperature == 0.5
	assert config.llm.max_tokens == 321
