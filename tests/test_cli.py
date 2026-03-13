from pathlib import Path
from unittest.mock import patch

import pytest

from llm_mddocgen.cli import main


def _write(path: Path, text: str) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text, encoding="utf-8")


TASK_MD = "---\nname: weekly-digest\npersona: research-analyst\ntemplate: report\n---\n\n# Objective\n- Summarize this week.\n"
PERSONA_MD = "---\nname: research-analyst\n---\n\n# Identity\nResearch specialist.\n"
PROJECT_MD = "---\nname: test-project\ndescription: a test project\n---\n\n# Objective\nDo the thing.\n"


def _make_persona(personas_dir: Path) -> None:
	_write(personas_dir / "research-analyst" / "persona.md", PERSONA_MD)


def _make_config(tmp_path: Path, personas_root: Path) -> Path:
	internal_root = tmp_path / ".llm-mddocgen"
	config_path = tmp_path / "llm_mddocgen.toml"
	config_path.write_text(
		f'personas_root = "{personas_root}"\ninternal_root = "{internal_root}"\n',
		encoding="utf-8",
	)
	return config_path


def test_cli_generates_report_and_internal_state(tmp_path: Path) -> None:
	personas_dir = tmp_path / "personas"
	_write(
		personas_dir / "research-analyst" / "persona.md",
		"---\nname: research-analyst\n---\n\n# Identity\nResearch specialist.\n",
	)
	_write(
		personas_dir / "research-analyst" / "data" / "reference.md",
		"- prioritize evidence\n- compare source quality\n",
	)

	task_dir = tmp_path / "tasks" / "weekly-digest"
	_write(task_dir / "task.md", TASK_MD)
	_write(task_dir / "notes.md", "- Team is blocked on deployment.\n")

	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			str(task_dir / "task.md"),
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0

	reports = list((output_dir / "tasks").glob("weekly-digest-*.md"))
	assert len(reports) == 1
	logs = list((output_dir / "logs").glob("weekly-digest-*.log.md"))
	assert len(logs) == 1
	log_text = logs[0].read_text(encoding="utf-8")
	assert "# Sources" in log_text

	# run log uses a bare timestamp name (no task name prefix)
	run_logs = [p for p in (output_dir / "logs").glob("*.md") if not p.name.endswith(".log.md")]
	assert len(run_logs) == 1
	run_log_text = run_logs[0].read_text(encoding="utf-8")
	assert "status: success" in run_log_text

	internal_root = tmp_path / ".llm-mddocgen"
	manifests = list((internal_root / "manifests").glob("weekly-digest-*.json"))
	assert len(manifests) == 1
	assert (internal_root / "state" / "last_run.json").exists()


def test_cli_fails_task_when_persona_missing_and_logs_failure(tmp_path: Path) -> None:
	task_dir = tmp_path / "tasks" / "broken-task"
	_write(task_dir / "task.md", "---\nname: broken-task\npersona: missing-persona\ntemplate: report\n---\n\n# Objective\nNeed help.\n")

	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			str(task_dir / "task.md"),
			"--config", str(tmp_path / "missing.toml"),
			"--output-path", str(output_dir),
		])
	assert exit_code == 1

	reports = list(output_dir.glob("**/*.md")) if output_dir.exists() else []
	# only the run log should exist (no report for failed task)
	log_files = [p for p in reports if p.parent.name == "logs"]
	assert all(p in log_files for p in reports)

	run_logs = [p for p in (output_dir / "logs").glob("*.md") if not p.name.endswith(".log.md")]
	assert len(run_logs) == 1
	run_log_text = run_logs[0].read_text(encoding="utf-8")
	assert "status: failed" in run_log_text
	assert "cannot be resolved" in run_log_text


def test_cli_task_flag_runs_single_file(tmp_path: Path) -> None:
	personas_dir = tmp_path / "personas"
	_make_persona(personas_dir)
	task_file = tmp_path / "weekly-digest.md"
	_write(task_file, TASK_MD)
	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--task", str(task_file),
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0
	assert len(list((output_dir / "tasks").glob("weekly-digest-*.md"))) == 1


def test_cli_task_with_project_flag(tmp_path: Path) -> None:
	personas_dir = tmp_path / "personas"
	_make_persona(personas_dir)
	task_file = tmp_path / "weekly-digest.md"
	project_file = tmp_path / "test-project.md"
	_write(task_file, TASK_MD)
	_write(project_file, PROJECT_MD)
	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--task", str(task_file),
			"--project", str(project_file),
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0
	# project runs go under output/projects/<project-name>/
	assert len(list((output_dir / "projects" / "test-project").glob("weekly-digest-*.md"))) == 1


def test_cli_project_without_task_is_error(tmp_path: Path) -> None:
	project_file = tmp_path / "test-project.md"
	_write(project_file, PROJECT_MD)

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--project", str(project_file),
			"--config", str(tmp_path / "missing.toml"),
			"--output-path", str(tmp_path / "output"),
		])
	assert exit_code == 2


def test_cli_task_flag_missing_file_is_error(tmp_path: Path) -> None:
	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--task", str(tmp_path / "nonexistent.md"),
			"--config", str(tmp_path / "missing.toml"),
			"--output-path", str(tmp_path / "output"),
		])
	assert exit_code == 2


def test_cli_project_flag_missing_file_is_error(tmp_path: Path) -> None:
	task_file = tmp_path / "weekly-digest.md"
	_write(task_file, TASK_MD)

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--task", str(task_file),
			"--project", str(tmp_path / "nonexistent.md"),
			"--config", str(tmp_path / "missing.toml"),
			"--output-path", str(tmp_path / "output"),
		])
	assert exit_code == 2


def test_cli_dry_run_shows_tasks_without_running(tmp_path: Path, capsys) -> None:
	personas_dir = tmp_path / "personas"
	_make_persona(personas_dir)
	task_dir = tmp_path / "tasks" / "weekly-digest"
	_write(task_dir / "task.md", TASK_MD)
	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--tasks-dir", str(tmp_path / "tasks"),
			"--dry-run",
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0
	assert not output_dir.exists()
	out = capsys.readouterr().out
	assert "weekly-digest" in out
	assert "research-analyst" in out


def test_cli_auto_discovers_tasks_directory(tmp_path: Path, monkeypatch) -> None:
	personas_dir = tmp_path / "personas"
	_make_persona(personas_dir)
	task_dir = tmp_path / "tasks" / "weekly-digest"
	_write(task_dir / "task.md", TASK_MD)
	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	monkeypatch.chdir(tmp_path)

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0
	assert len(list((output_dir / "tasks").glob("weekly-digest-*.md"))) == 1


def test_cli_no_tasks_found_is_error(tmp_path: Path, monkeypatch, capsys) -> None:
	monkeypatch.chdir(tmp_path)

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--config", str(tmp_path / "missing.toml"),
			"--output-path", str(tmp_path / "output"),
		])
	assert exit_code == 2
	captured = capsys.readouterr()
	assert "no tasks" in captured.err.lower()


def test_cli_project_dir_flag_sets_projects_root(tmp_path: Path) -> None:
	personas_dir = tmp_path / "personas"
	_make_persona(personas_dir)
	projects_dir = tmp_path / "projects"
	_write(projects_dir / "test-project.md", PROJECT_MD)

	task_md = "---\nname: weekly-digest\npersona: research-analyst\ntemplate: report\nproject: test-project\n---\n\n# Objective\nSummarize.\n"
	task_file = tmp_path / "weekly-digest.md"
	_write(task_file, task_md)
	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--task", str(task_file),
			"--project-dir", str(projects_dir),
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0
	assert len(list((output_dir / "projects" / "test-project").glob("weekly-digest-*.md"))) == 1


def test_cli_tags_from_task_and_persona_appear_in_report(tmp_path: Path) -> None:
	personas_dir = tmp_path / "personas"
	_write(
		personas_dir / "research-analyst" / "persona.md",
		"---\nname: research-analyst\ntags: [persona-tag]\n---\n\n# Identity\nResearch specialist.\n",
	)
	task_dir = tmp_path / "tasks" / "weekly-digest"
	_write(
		task_dir / "task.md",
		"---\nname: weekly-digest\npersona: research-analyst\ntemplate: report\ntags: [task-tag, shared-tag]\n---\n\n# Objective\nSummarize.\n",
	)
	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--task", str(task_dir / "task.md"),
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0

	reports = list((output_dir / "tasks").glob("weekly-digest-*.md"))
	assert len(reports) == 1
	content = reports[0].read_text(encoding="utf-8")
	assert content.startswith("---\n")
	assert "- task-tag" in content
	assert "- shared-tag" in content
	assert "- persona-tag" in content


def test_cli_disabled_task_is_skipped(tmp_path: Path, capsys) -> None:
	personas_dir = tmp_path / "personas"
	_make_persona(personas_dir)
	task_dir = tmp_path / "tasks" / "weekly-digest"
	_write(
		task_dir / "task.md",
		"---\nname: weekly-digest\npersona: research-analyst\ntemplate: report\nenabled: false\n---\n\n# Objective\nSummarize.\n",
	)
	config_path = _make_config(tmp_path, personas_dir)
	output_dir = tmp_path / "output"

	with patch("llm_mddocgen.config._seed_defaults"):
		exit_code = main([
			"--task", str(task_dir / "task.md"),
			"--config", str(config_path),
			"--output-path", str(output_dir),
		])
	assert exit_code == 0
	assert not list((output_dir / "tasks").glob("weekly-digest-*.md"))
	out = capsys.readouterr().out
	assert "skipped" in out
