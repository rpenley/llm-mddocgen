# Text generation for task reports.
# Contains both the LLM-backed path and the deterministic fallback synthesizer.

from .models import GlobalConfig, PersonaDefinition, SourceDocument, TaskDefinition
from .synthesis.runner import build_model_client

_MAX_SOURCES_IN_PROMPT = 30      # source documents included in LLM prompt
_MAX_LINES_PER_SOURCE = 40       # lines of each source excerpt sent to LLM
_MAX_PROFILE_LINES = 20          # lines of profile text included per source
_FALLBACK_TOP_FINDINGS = 8       # total findings pool for fallback report
_FALLBACK_PRIORITY_COUNT = 4     # findings used as active priorities
_FALLBACK_BLOCKER_SLICE = 7      # findings[_FALLBACK_PRIORITY_COUNT:_FALLBACK_BLOCKER_SLICE] = blockers


def _extract_bullets(text: str, limit: int = 6) -> list[str]:
	bullets: list[str] = []
	for line in text.splitlines():
		stripped = line.strip()
		if stripped.startswith(("- ", "* ")):
			bullets.append(stripped[2:].strip())
			if len(bullets) >= limit:
				break
	if bullets:
		return bullets

	# If no markdown bullets found, fall back to the first non-header, non-separator lines.
	fallback: list[str] = []
	for line in text.splitlines():
		stripped = line.strip()
		if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
			fallback.append(stripped)
			if len(fallback) >= limit:
				break
	return fallback


def _load_global_guardrails(config: GlobalConfig) -> str:
	if config.global_file and config.global_file.exists():
		return config.global_file.read_text(encoding="utf-8").strip()
	return ""


def _build_prompt(task: TaskDefinition, persona: PersonaDefinition, sources: list[SourceDocument], config: GlobalConfig) -> tuple[str, str]:
	system_parts = [
		f"You are the {persona.name} persona.",
		persona.body.strip(),
		"Write concise, practical markdown with explicit uncertainty. Do not fabricate facts.",
	]
	guardrails = _load_global_guardrails(config)
	if guardrails:
		system_parts.append(guardrails)
	system_prompt = "\n\n".join(system_parts)

	profile_sources = [s for s in sources if s.scope == "profile"]
	other_sources = [s for s in sources if s.scope != "profile"]

	parts: list[str] = [f"Task name: {task.name}"]

	if task.project_definition is not None:
		project_context = f"Project: {task.project_definition.name}"
		if task.project_definition.body.strip():
			project_context += f"\n\n{task.project_definition.body.strip()}"
		parts.append(project_context)
	elif task.project_name:
		parts.append(f"Project: {task.project_name}")

	if task.task_template:
		template_label = f"Task template: {task.task_template}"
		if task.template_definition is not None:
			template_label += f"\n\n{task.template_definition.body.strip()}"
		parts.append(template_label)

	if profile_sources:
		profile_lines: list[str] = []
		for src in profile_sources:
			profile_lines.append("\n".join(src.text.splitlines()[:_MAX_PROFILE_LINES]))
		parts.append(
			"User profile — preferences and context of the person requesting this task:\n\n"
			+ "\n\n".join(profile_lines)
		)

	scoped_sources: list[str] = []
	for src in other_sources[:_MAX_SOURCES_IN_PROMPT]:
		excerpt = "\n".join(src.text.splitlines()[:_MAX_LINES_PER_SOURCE])
		scoped_sources.append(f"[{src.scope}] {src.path}\n{excerpt}")

	parts.extend([
		"Task definition:",
		task.body,
		"Retrieved source excerpts:",
		"\n\n".join(scoped_sources),
	])

	if task.template_definition is not None:
		parts.append(f"Produce output appropriate for a {task.task_template} as described in the task template above.")
	else:
		parts.append(
			"Produce markdown with these sections in order: "
			"# Summary, # Active Priorities, # Concerns and Blockers, "
			"# Suggested Next Actions, # Unresolved Questions."
		)

	return system_prompt, "\n\n".join(parts)


def _fallback_report(task: TaskDefinition, persona: PersonaDefinition, sources: list[SourceDocument]) -> str:
	task_points = _extract_bullets(task.body)
	persona_points = _extract_bullets(persona.body)

	profile_points: list[str] = []
	persona_data_points: list[str] = []
	task_data_points: list[str] = []
	for source in sources:
		if source.scope == "profile" and len(profile_points) < 4:
			profile_points.extend(_extract_bullets(source.text, limit=2))
		if source.scope == "persona" and source.path != persona.persona_file and len(persona_data_points) < 4:
			persona_data_points.extend(_extract_bullets(source.text, limit=2))
		if source.scope == "task" and source.path != task.task_file and len(task_data_points) < 4:
			task_data_points.extend(_extract_bullets(source.text, limit=2))

	top_findings = (task_points + task_data_points + persona_data_points + profile_points)[:_FALLBACK_TOP_FINDINGS]
	if not top_findings:
		top_findings = ["No explicit bullet points found in source material."]

	priority_items = top_findings[:_FALLBACK_PRIORITY_COUNT]
	blocker_items = top_findings[_FALLBACK_PRIORITY_COUNT:_FALLBACK_BLOCKER_SLICE] or ["Potential ambiguity in current source material."]

	actions: list[str] = []
	for item in priority_items:
		actions.append(f"Convert into an actionable step: {item}")
	if not actions:
		actions = ["Refresh task and profile files with clearer required outcomes."]

	question_items: list[str] = []
	for line in task.body.splitlines():
		stripped = line.strip()
		if stripped.endswith("?"):
			question_items.append(stripped)
		if len(question_items) >= 5:
			break
	if not question_items:
		question_items = ["Which assumptions in this digest need explicit verification?"]

	findings_block = "\n".join(f"- {item}" for item in top_findings)
	priorities_block = "\n".join(f"- {item}" for item in priority_items)
	blockers_block = "\n".join(f"- {item}" for item in blocker_items)
	actions_block = "\n".join(f"- {item}" for item in actions)
	questions_block = "\n".join(f"- {item}" for item in question_items)

	return "\n".join(
		[
			"# Summary",
			"",
			f"Task: {task.name}",
			f"Persona: {persona.name}",
			"",
			"## Key Findings",
			findings_block,
			"",
			"# Active Priorities",
			priorities_block,
			"",
			"# Concerns and Blockers",
			blockers_block,
			"",
			"# Suggested Next Actions",
			actions_block,
			"",
			"# Unresolved Questions",
			questions_block,
			"",
			"# Source Coverage",
			f"- Total source files used: {len(sources)}",
			"- This run used source retrieval from task, persona, profile, and optional prior generated output.",
		]
	).strip() + "\n"


def _generate_report(task: TaskDefinition, persona: PersonaDefinition, sources: list[SourceDocument], config: GlobalConfig) -> tuple[str, str, str]:
	model_client = build_model_client(config)
	if model_client is None:
		return _fallback_report(task, persona, sources), "fallback", ""

	try:
		system_prompt, user_prompt = _build_prompt(task, persona, sources, config)
		response, thinking = model_client.complete(system_prompt, user_prompt)
		response = response.strip()
		if not response:
			raise RuntimeError("llm returned empty report")
		return response + "\n", model_client.label(), thinking
	except Exception as exc:
		# Keep local-first execution resilient even when the configured model endpoint is unavailable.
		report = _fallback_report(task, persona, sources)
		return report, f"fallback-after-llm-error:{exc}", ""
