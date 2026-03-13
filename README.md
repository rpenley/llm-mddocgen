# Large Language Model Markdown Document Generator (llm-mddocgen)

llm-mddocgen is a markdown based prompt builder for generating documents with large language models.

llm-mddocgen connects to any OpenAI-compatible LLM backend and produces reports, summaries, research documents, code, and more — driven by a configured set of tasks. It is not a chatbot or an agentic system. Markdown, text, and pdf data goes in, an LLM generated document comes out.

---

## Philosophy

```
task + persona + template + sources → LLM synthesis → output document
```
llm-mddocgen is a **one-directional pipeline**. There is no interactive loop, it treats your model like a compiler. If the output needs adjustment, edit your task, persona, or template and run again. The goal is to produce reliable definitions of what you want to generate and get a progressivly better collection of documents or queue up various projects and questions and generate weekly digests to review on demand.


---

## Getting Started

The fastest way to understand llm-mddocgen is to look at the `examples/` directory. It contains example tasks and projects which you can copy to another location to get started. Copy the llm-mddocgen.toml.example to the location where you execute llm-mddocgen and configure your backend against it, then provide a task and project or if you have multiple you can provide a task-dir and/or project-dir, projects are optional if your task does not define one.

```bash
llm-mkdocgen --help

llm-mddocgen --task examples/tasks/roman-statesmen.md
llm-mddocgen --tasks-dir examples/tasks/
llm-mddocgen --task examples/tasks/marcus-agrippa-life-summary.md --project examples/projects/marcus-agrippa-research.md
```

Use `--dry-run` to preview what would run without calling the model:

```bash
llm-mddocgen --tasks-dir examples/tasks/ --dry-run
```


---

## Core Concepts

### Tasks

A task is a unit of work — a document you want generated. Each task is a markdown file with a YAML frontmatter block that declares which persona should perform the work and which template defines the output format.

```yaml
---
name: roman-statesmen
persona: historian
template: report
tags: [history, rome]
---

Produce a structured list of famous Roman statesmen and their accomplishments,
spanning the Republic and Imperial periods.
```

Required frontmatter fields: `name`, `persona`, `template`. Optional fields:

| Field | Description |
|-------|-------------|
| `project` | Links the task to a shared project context |
| `tags` | One or more tags merged into the output document's frontmatter |
| `enabled` | Set to `false` to skip this task without deleting it (default: `true`) |

The body of the task file is passed directly to the model as the user prompt. Any other `.md` or `.txt` files in the same task directory are automatically collected and injected as source material.

### Personas

A persona is a role definition — it becomes the system prompt for the model. Each persona is a markdown file with a YAML frontmatter block and a body that describes the expert's behavior, style, and priorities.

```yaml
---
name: my-analyst
description: Evaluates source material and surfaces key findings.
personality: direct, skeptical, evidence-oriented
behavior:
  - lead with the strongest supported findings
  - distinguish confident conclusions from inferences
  - flag gaps and unresolved questions explicitly
---

You are a research analyst. Your job is to evaluate sources, identify the
strongest claims, and surface gaps in the available evidence.

Distinguish primary from secondary sources. Flag uncertainty explicitly
rather than smoothing it over.
```

Personas live in `personas/<name>/persona.md` (directory layout) or as a flat `personas/<name>.md` file. Files placed in `personas/<name>/data/` are injected as source material on every run of that persona. A `tags` field in persona frontmatter is merged into the output's tag list.

A full set of built-in personas is included — see the table below. Use them as-is or copy one as a starting point for a custom persona.

### Templates

A template is an output format contract. It defines the sections, structure, and style a generated document must follow. Templates are reusable across tasks.

```yaml
---
name: brief
default_persona: analyst
tags: [brief]
---

Produce a short, focused brief. Essential information only.

Required sections:
- **Brief** — two to four sentence summary of the situation
- **Key Facts** — three to five bullets, each a single concrete claim
- **Recommendation** — one clear action or conclusion
```

When a task sets `template: brief`, the template body is appended to the user prompt. If `default_persona` is set, it is used when the task has no `persona` field.

A full set of built-in templates is included — see the table below.

### Projects

A project is a shared context for a group of related tasks — an optional markdown file with a YAML frontmatter block and a body that provides standing background relevant to multiple tasks.

```yaml
---
name: marcus-agrippa-research
description: Research on the life, career, and legacy of Marcus Vipsanius Agrippa
---

Produce a comprehensive research paper on Marcus Vipsanius Agrippa —
the Roman general, statesman, and close ally of Augustus Caesar.
```

Tasks reference a project via the `project:` frontmatter field. Project content is injected as source material alongside task-specific sources. Projects live in a `projects/` directory at the project root. A `tags` field in project frontmatter is merged into the output's tag list.

### Tags and Output Frontmatter

Any `tags` field defined in a task, persona, template, or project is collected and merged into the generated document as YAML frontmatter. Duplicate tags are removed. If no tags are defined anywhere, no frontmatter is added.

```yaml
---
tags:
  - history
  - rome
  - report
---

# Roman Statesmen
...
```

This makes llm-mddocgen output compatible with tools like Obsidian that read tags from document frontmatter.

---

## Built-in Personas

| Name | Description |
|------|-------------|
| `advisor` | Practical, patient life and decision advisor focused on frugality, quality, and long-term wellbeing |
| `analyst` | Objective and data-driven with a focus on measurable results |
| `coder` | Explains software systems, produces code examples, and evaluates design tradeoffs |
| `copywriter` | Engaging, narrative-focused writer with a focus on improving writing and prose quality |
| `critic` | Rigorous, logic-testing skeptic designed to find flaws in arguments or ideas |
| `diplomat` | Empathetic, fair-minded mediator for navigating difficult human interactions |
| `educator` | Patient and focused on building understanding through clear, simple explanations |
| `engineer` | Technical, systems-focused, and concerned with real-world implementation constraints |
| `historian` | Produces factual, sourced accounts of historical events and individuals |
| `manager` | Execution-oriented organizer focused on unblocking dependencies and making decisions |
| `researcher` | Synthesizes source material into structured research documents on any topic |
| `strategist` | High-level, risk-aware planner focused on trade-offs and long-term impacts |
| `writer` | Produces clear, well-structured prose for documents, articles, and reports |

## Built-in Templates

| Name | Description |
|------|-------------|
| `analysis` | Analytical breakdown that interprets evidence and produces a defensible judgment |
| `assessment` | Balanced evaluation of opposing sides of a core dilemma with pros and cons |
| `brief` | Short decision-support document with essential facts and a single clear recommendation |
| `code` | Complete, runnable source code implementation with explanation and known limitations |
| `critique` | Critical evaluation with specific strengths, weaknesses, and a clear overall verdict |
| `decision` | Factor-by-factor comparison of multiple choices to force a logical verdict |
| `design` | Structured design document defining components, interfaces, constraints, and open questions |
| `detailed` | Comprehensive, exhaustive breakdown with deep and granular detail |
| `draft` | Structured interpersonal correspondence with tone-setting and a clear purpose |
| `instruct` | Sequential, actionable instructions with prerequisites and success criteria |
| `plan` | Time-based organization into daily priorities and milestones toward a goal |
| `proofread` | Line-level proofreading with structural feedback and a clear revision verdict |
| `question` | Anticipated question-and-answer pairs extracted from raw source material |
| `recommend` | Decision-focused recommendation for an approach or outcome |
| `report` | Formal structured report with background, findings, analysis, and conclusions |
| `research` | Research document surfacing what is known, uncertain, and still missing on a topic |
| `review` | Opinionated breakdown of media and products with general consensus and a final score |
| `summary` | Bottom-line up front, key takeaways, and a final recommendation |

Custom personas and templates can be added to `~/.llm-mddocgen/custom/personas/` and `~/.llm-mddocgen/custom/templates/`. User-defined files override built-ins with the same name.

---

## Workspace Layout

```
llm-mddocgen.toml         # Per-project config (optional; overrides ~/.llm-mddocgen/config.toml)
personas/                 # Custom persona definitions (optional)
  <name>/
    persona.md            # Required: system prompt + frontmatter
    data/                 # Optional: source files injected on every run
templates/                # Custom template definitions (optional)
  <name>.md
tasks/                    # Task definitions
  <name>/
    task.md               # Required: task body + frontmatter
    *.md / *.txt          # Optional: source files injected into this task
projects/                 # Shared project context files (optional)
  <name>.md
profile/                  # Standing user context injected into every run
  default/
    profile.md            # Max 20 lines; use --profile <name> for alternates
output/                   # Output reports (written by llm-mddocgen; resolved from CWD)
  tasks/
    <task-name>-<timestamp>.md
  projects/
    <project-name>/
      <task-name>-<timestamp>.md
  logs/
    <timestamp>.md        # Per-task generation logs and run summaries
```

Global config and built-in assets live at `~/.llm-mddocgen/`.

---

## Install

### Recommended: uv

[uv](https://docs.astral.sh/uv/) manages the virtualenv automatically — no activation step needed.

```bash
# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and run
uv sync
uv run python -m llm_mddocgen --help

# Install as a system command
uv tool install .
llm-mddocgen --version
```

### PyPI

```bash
pip install llm-mddocgen
llm-mddocgen --version
```

### pip (from source)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
llm-mddocgen --version
```

### Docker

```bash
# Runs against the examples/ directory by default
docker compose up

# Run against a custom workspace
WORKSPACE_PATH=/path/to/your/tasks docker compose up
```

---

## Configuration

llm-mddocgen loads config from one of two places:

- **`./llm-mddocgen.toml`** — used if present in the current directory; global config is ignored
- **`~/.llm-mddocgen/config.toml`** — global fallback

Copy `llm-mddocgen.toml.sample` to get started:

```toml
# Per-project config. Values here override the global ~/.llm-mddocgen/config.toml.

# Uncomment to use project-local persona/template directories.
# personas_root = "personas"
# templates_root = "templates"

# Profile root for standing user context injected into every prompt.
# profile_root = "profile"

# Projects root for task-scoped shared context.
# projects_root = "projects"

# Output directory. Resolved relative to the current working directory.
generated_root = "output"

[llm]
# Set to true to enable LLM synthesis. False uses the deterministic fallback.
enabled = false

# Any OpenAI-compatible endpoint: Ollama, vLLM, OpenAI, etc.
base_url = "http://localhost:11434/v1"
model = "llama3.2"

# Auth key (or use LLM_MDDOCGEN_API_KEY env var).
api_key = ""

# Request tuning. Suggested starting points by provider:
#   Ollama (llama3, mistral)  — temperature = 0.2,  max_tokens = 1200
#   Qwen3 standard            — temperature = 0.2,  max_tokens = 4096
#   Qwen3 thinking mode       — temperature = 0.7,  max_tokens = 10000
#   OpenAI gpt-4o             — temperature = 0.3,  max_tokens = 2048
timeout_seconds = 60
temperature = 0.2
max_tokens = 1200

# Web search via tool use (requires a model that supports function calling, e.g. llama3.1+).
# llm-mddocgen asks the model to generate search queries, fetches results from DuckDuckGo,
# and injects them as source documents before synthesis.
# web_search = false
# web_search_max_queries = 3
# web_search_max_results = 5

# Save model reasoning output (<think>...</think> blocks) to a separate file.
# thinking_output = false
```

---

## Quick Start

**1. Point llm-mddocgen at your LLM.**

Edit `llm-mddocgen.toml` with your endpoint and model, or set `enabled = false` to use the deterministic fallback (good for testing workspace structure without a running model).

**2. Try the examples.**

```bash
llm-mddocgen --tasks-dir examples/tasks/
```

Or scaffold a new task from scratch:

```bash
llm-mddocgen --init-task tasks/my-first-task/task.md
```

Edit the scaffolded file to set your `persona`, `template`, and task body.

**3. Run it.**

```bash
llm-mddocgen --task tasks/my-first-task/task.md
```

**4. Read the output.**

Reports land in `output/tasks/` for standalone tasks, or `output/projects/<name>/` for project-linked tasks.

---

## CLI Reference

### Task execution

| Flag | Description |
|------|-------------|
| `--task <path>` | Task file to run (repeatable) |
| `--tasks-dir <path>` | Run all tasks found in a directory |
| `--project <path>` | Project file to associate with `--task` |
| `--project-dir <path>` | Directory of project files for auto-association |
| `--fail-fast` | Stop on the first task failure |

### Output and profile

| Flag | Description |
|------|-------------|
| `--output-path <path>` | Override the output directory |
| `--profile <name>` | Load a named profile from the profile root |
| `--profile-path <path>` | Override the profile root directory |

### Configuration

| Flag | Description |
|------|-------------|
| `--config <path>` | Use a specific TOML config file |

### Utility actions

| Flag | Description |
|------|-------------|
| `--list personas\|tasks\|templates` | List available personas, tasks, or templates |
| `--init-task <path>` | Write a starter task.md and exit |
| `--dry-run` | Show what would run without executing |
| `--version` | Print version and exit |

---

## Source Injection

On each run, llm-mddocgen collects source documents from several locations and injects them into the prompt:

| Source | Content |
|--------|---------|
| Task directory | All `.md` and `.txt` files alongside `task.md` |
| Task `data/` | Subdirectory of supporting files |
| Persona `data/` | Reference files for the active persona |
| Project file | Shared context declared in `project:` frontmatter |
| Profile | Standing user context from `profile/default/profile.md` |
| Previous output | The most recent generated report for this task (for iterative refinement) |
| Web search | DuckDuckGo results fetched via tool use (if enabled) |

PDF files are supported when `allow_pdf_materials = true` in config.

---

## Profile

The profile is a standing context document injected into every task run. Use it for user identity, preferences, or constraints that apply across all your tasks.

```markdown
I am a software engineer at a mid-stage startup. I prefer direct, no-hedging analysis.
Assume I have strong technical context and skip basic explanations.
Prioritize actionable output over comprehensive coverage.
```

- Location: `profile/default/profile.md`
- Maximum 20 lines (enforced)
- Use `--profile <name>` to load an alternate profile from `profile/<name>/profile.md`

---

## Fallback Mode

When `llm.enabled = false` (the default), llm-mddocgen uses a deterministic fallback synthesizer. It extracts bullet points from source files and structures them into a fixed-section report. No model is called. This is useful for testing your workspace configuration and verifying that sources are collected correctly before connecting an LLM.

---

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest -q

# Install as a system command
uv tool install .
```

Dev dependencies are declared using PEP 735 dependency groups in `pyproject.toml`. Use `uv sync --dev` — not `pip install -e ".[dev]"` — to install them.
