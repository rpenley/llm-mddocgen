---
name: instruct
objective: Sequential, actionable instructions with prerequisites and success criteria.
format: numbered steps with supporting sections
layout:
  - Purpose
  - Prerequisites
  - Steps
  - Verification
  - Gotchas and Common Mistakes
context: Use when the output must be executable — something a reader can follow to accomplish a specific outcome. Good for how-to guides, setup procedures, operational runbooks, and tutorials.
scope: Every step must be actionable. Avoid explaining why in the middle of steps — put background in prerequisites or notes. Include failure conditions and what to do about them.
reference: Use detailed for conceptual depth. Use plan for time-based goal organization.
---
Produce step-by-step instructions that a reader can follow to accomplish a specific outcome.

Required output sections:
- **# Purpose** — one sentence stating what these instructions accomplish and what the end state looks like
- **# Prerequisites** — what must be true, installed, or available before starting; list format
- **# Steps** — numbered sequential instructions; each step is a single, concrete action; use sub-steps where necessary; do not combine unrelated actions into one step
- **# Verification** — how to confirm the steps worked; what a successful outcome looks like
- **# Gotchas and Common Mistakes** — known failure modes, easy errors, and how to recover from them

Steps must be specific enough to execute without guessing. Do not skip steps that seem obvious — include them. Number every step.
