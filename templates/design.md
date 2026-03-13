---
name: design
objective: Structured design document defining components, interfaces, constraints, and open questions before implementation.
format: markdown design document
layout:
  - Problem Statement
  - Goals and Non-Goals
  - Design Overview
  - Components and Interfaces
  - Data and State
  - Trade-offs and Alternatives
  - Open Questions
context: Use when planning a system, feature, or architecture before building it. Applies to software design, product design, process design, or any structured system where decisions need to be made explicit before execution begins.
scope: A design document defines what will be built and why, not how to build it step by step. Stop at the point where implementation begins. Open questions must be named and assigned.
reference: Use instruction for step-by-step execution after the design is settled. Use detailed for deep explanatory coverage of an existing system. Use decision for a focused multi-option comparison.
---
Produce a design document that makes the key decisions explicit before implementation begins.

Required output sections:
- **# Problem Statement** — what is being designed and why; the need or gap this design addresses
- **# Goals and Non-Goals** — what this design must accomplish (goals) and what it deliberately does not address (non-goals); list format for both
- **# Design Overview** — a high-level description of the proposed design; include a diagram (ASCII or Mermaid) when structure or flow benefits from visualization
- **# Components and Interfaces** — the major parts of the design, what each does, and how they interact; use one subsection per component for complex designs
- **# Data and State** — what data the design produces, consumes, or transforms; how state is managed; what persists and what is ephemeral
- **# Trade-offs and Alternatives** — approaches that were considered and rejected; why the chosen design is preferred; what it costs
- **# Open Questions** — decisions not yet made, dependencies not yet resolved, or risks not yet mitigated; each with a note on who owns it or what information would resolve it

The design must be specific enough that a reader could implement it without needing to make major architectural decisions themselves.
