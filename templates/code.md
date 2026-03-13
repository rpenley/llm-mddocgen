---
name: code
objective: Complete, runnable source code implementation with explanation and known limitations.
format: source code with supporting prose
layout:
  - Implementation
  - How It Works
  - Assumptions
  - Known Limitations
context: Use when the deliverable is working code, not a plan or description of code. Applies across languages and domains — systems code, scripts, web code, data pipelines, or any other software implementation task.
scope: Code is the primary deliverable. Prose exists to explain non-obvious decisions, not to describe what the code does line-by-line. Do not add scaffolding, tests, or wrappers that were not requested.
reference: Use instruction for step-by-step procedural guidance. Use detailed for deep technical explanation without a code deliverable.
---
Produce working source code that fulfills the task objective. The output is a complete, runnable implementation — not a plan, not a sketch. Code is the deliverable.

Required output sections:
- **# Implementation** — the complete source code in one or more fenced code blocks labeled with the language and filename
- **# How It Works** — brief prose explaining the structure and key decisions; focus on non-obvious logic; do not narrate the obvious
- **# Assumptions** — any ambiguities in the task that required an interpretation, and what was chosen
- **# Known Limitations** — anything the implementation does not handle, edge cases ignored, or known deficiencies

Write production-quality code within the constraints of the task. Prefer clarity over cleverness. If the task is underspecified, state the interpretation used in Assumptions and produce the most useful implementation that interpretation supports.
