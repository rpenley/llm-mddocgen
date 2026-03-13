"""Structural constants for llm-mddocgen's workspace layout and file conventions."""

# Canonical file names for workspace entities
TASK_FILE = "task.md"
PERSONA_FILE = "persona.md"
PROJECT_FILE = "project.md"

# Canonical subdirectory names
DATA_DIR = "data"

# File matching
README_STEM = "readme"
MARKDOWN_EXTENSION = ".md"
PDF_EXTENSION = ".pdf"
SOURCE_EXTENSIONS = frozenset({".md", ".txt"})
SOURCE_EXTENSIONS_WITH_PDF = frozenset({".md", ".txt", ".pdf"})

# Output directory layout (subdirs under generated_root)
OUTPUT_TASKS_DIR = "tasks"
OUTPUT_PROJECTS_DIR = "projects"
OUTPUT_LOGS_DIR = "logs"
