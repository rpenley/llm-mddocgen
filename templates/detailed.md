---
name: detailed
objective: Comprehensive, exhaustive breakdown with deep and granular detail.
format: markdown document with multiple subsections
layout:
  - Overview
  - Background
  - Detailed Breakdown (with subsections)
  - Edge Cases and Exceptions
  - Gaps and Unknowns
context: Use when the reader needs to understand a topic thoroughly, not just at a summary level. Good for technical documentation, deep research, onboarding material, and reference documents.
scope: Depth over brevity. Cover components, mechanisms, exceptions, and edge cases. Subsections are expected and encouraged. Do not compress or abbreviate where detail serves understanding.
reference: Use summary for a concise version. Use instruction for step-by-step procedural detail.
---
Produce a comprehensive, deeply detailed breakdown of the subject. Do not summarize when you can explain. Do not simplify when nuance matters.

Required output sections:
- **# Overview** — what this document covers and why it warrants exhaustive treatment
- **# Background** — history, prerequisites, and foundational context the reader needs
- **# Detailed Breakdown** — the main body; use `##` subsections to organize distinct components, mechanisms, phases, or dimensions; each subsection should go deep
- **# Edge Cases and Exceptions** — behaviors, conditions, or scenarios that deviate from the norm
- **# Gaps and Unknowns** — areas where the available material is incomplete or where further investigation would add depth

Err toward more detail rather than less. Use subsections aggressively to maintain readability. Completeness is the primary goal.
