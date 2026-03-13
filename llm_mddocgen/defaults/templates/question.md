---
name: question
objective: Anticipated question-and-answer pairs extracted from raw source material.
format: Q&A pairs in markdown
layout:
  - Overview
  - Questions and Answers
  - Unanswered Questions
context: Use when source material contains information that is best surfaced as answers to likely questions. Good for FAQ generation, study guides, interview prep, and knowledge base creation.
scope: Questions must be ones a real reader would ask. Answers must be grounded in the source material. Do not invent answers to questions the sources do not address.
reference: Use detailed for narrative breakdowns. Use summary for a synthesized overview rather than discrete Q&A.
---
Produce a set of question-and-answer pairs drawn from the source material. Questions should reflect what a curious, informed reader would actually ask.

Required output sections:
- **# Overview** — one paragraph describing what domain or topic the Q&A covers and what the source material addresses
- **# Questions and Answers** — a series of Q&A pairs formatted as:
  **Q: [question]**
  A: [answer grounded in source material]
  Aim for 8–15 pairs organized by theme if the material supports it.
- **# Unanswered Questions** — questions the source material raises but does not answer; list each with a brief note on what would be needed to answer it

Questions should be specific and answerable. Answers should be concise but complete. Do not pad with questions whose answers are trivial or already obvious.
