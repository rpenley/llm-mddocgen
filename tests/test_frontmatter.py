from pathlib import Path

from llm_mddocgen.frontmatter import read_markdown_with_frontmatter, write_markdown_with_frontmatter


def test_roundtrip_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    metadata = {"id": "cake", "mode": "web_allowed", "update": False}
    body = "# Title\n\nHello"

    write_markdown_with_frontmatter(path, metadata, body)
    loaded_meta, loaded_body = read_markdown_with_frontmatter(path)

    assert loaded_meta["id"] == "cake"
    assert loaded_meta["mode"] == "web_allowed"
    assert loaded_meta["update"] is False
    assert loaded_body.startswith("# Title")


def test_plain_markdown_without_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "plain.md"
    path.write_text("no frontmatter", encoding="utf-8")

    metadata, body = read_markdown_with_frontmatter(path)
    assert metadata == {}
    assert body == "no frontmatter"
