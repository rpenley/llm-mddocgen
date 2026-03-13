from pathlib import Path

from llm_mddocgen.scanner import discover_personas, discover_tasks, filter_tasks


def test_discover_tasks_only_with_task_md(tmp_path: Path) -> None:
	valid = tmp_path / "valid"
	invalid = tmp_path / "invalid"
	valid.mkdir()
	invalid.mkdir()
	(valid / "task.md").write_text("---\npersona: demo\n---\n", encoding="utf-8")

	found = discover_tasks(tmp_path)
	assert [p.name for p in found] == ["valid"]


def test_discover_personas_only_with_persona_md(tmp_path: Path) -> None:
	builtin = tmp_path / "builtin"
	user = tmp_path / "user"
	valid = builtin / "analyst"
	invalid = builtin / "notes"
	valid.mkdir(parents=True)
	invalid.mkdir(parents=True)
	(valid / "persona.md").write_text("# Persona\n", encoding="utf-8")

	found = discover_personas(user, builtin)
	assert [p.name for p in found] == ["analyst"]


def test_discover_personas_user_overrides_builtin(tmp_path: Path) -> None:
	builtin = tmp_path / "builtin"
	user = tmp_path / "user"
	(builtin / "analyst").mkdir(parents=True)
	(builtin / "analyst" / "persona.md").write_text("# Builtin analyst\n", encoding="utf-8")
	(user / "analyst").mkdir(parents=True)
	(user / "analyst" / "persona.md").write_text("# User analyst\n", encoding="utf-8")

	found = discover_personas(user, builtin)
	assert len(found) == 1
	assert found[0].parent == user


def test_filter_tasks_selected(tmp_path: Path) -> None:
	a = tmp_path / "a"
	b = tmp_path / "b"
	a.mkdir()
	b.mkdir()

	selected = filter_tasks([a, b], ["b"])
	assert [p.name for p in selected] == ["b"]
