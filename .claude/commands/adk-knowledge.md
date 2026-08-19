# ADK Knowledge Provider

Provides Google ADK (Agent Development Kit) reference knowledge for architects and developers. Covers core concepts, patterns, API primitives, and project-specific conventions.

## When to use

- You need to look up ADK concepts, primitives, or patterns
- You need project-specific ADK conventions (Nexus proxy, LLM wrappers, session management)
- Trigger phrases: "ADK reference", "how does ADK handle…", "ADK best practice for…"

## Knowledge Sources

The project has three ADK knowledge sources, in this order of precedence:

1. **`google-agents-cli-*` skills** (installed in `.claude/skills/` by `agents-cli setup`) — the maintained Google reference for ADK and Agent Platform. Pick the matching skill:
   - `google-agents-cli-workflow` — lifecycle entrypoint, model selection, coding guidelines, troubleshooting
   - `google-agents-cli-adk-code` — agent types, tools, callbacks, state, orchestration patterns
   - `google-agents-cli-scaffold` — project templates, `scaffold create|enhance|upgrade`
   - `google-agents-cli-eval` — eval methodology, metrics, dataset schema
   - `google-agents-cli-deploy` — Agent Runtime / Cloud Run / GKE, CI/CD
   - `google-agents-cli-publish` — Gemini Enterprise, Agent Registry
   - `google-agents-cli-observability` — tracing, logging, analytics
2. **`.github/skills/adk-knowledge-provider/ADK_KNOWLEDGE.md`** — project-specific conventions (Nexus proxy, LLM wrappers, session management). Optional: if the file does not exist, note that project-specific conventions are unavailable.
3. **Context7 MCP** — `mcp__context7__resolve-library-id` with `google-adk`, then `mcp__context7__query-docs`. Use as a fallback when the skills do not cover the topic.

When answering questions:
1. Invoke the relevant `google-agents-cli-*` skill(s) via the Skill tool.
2. Read `ADK_KNOWLEDGE.md` (if present) to ground the answer in project conventions.
3. Fall back to Context7 only for gaps. If the MCP calls fail or return no results, note that official documentation could not be retrieved.
4. Cite the specific source and section for each claim. On conflict: `ADK_KNOWLEDGE.md` wins for project conventions, the `google-agents-cli-*` skills win for current ADK/Agent Platform behavior, Context7 for general API detail. Always note the discrepancy explicitly.
5. If no source covers the topic, respond with: "This topic is not covered in the project knowledge base or the retrieved documentation. The following is based on general reasoning and may not reflect current ADK behavior or project conventions:" then provide the best-effort answer.

## CLI Reference

Answers that involve running, testing, deploying, or publishing an agent must reference the `agents-cli` commands:
`create`, `scaffold`, `install`, `playground`, `run`, `lint`, `eval run|generate|grade|compare|analyze|optimize`, `eval dataset synthesize`, `eval metric list`, `deploy`, `publish gemini-enterprise`, `infra setup-cicd`, `login`, `cmd-info`, `update`.

Keep the skills current with `agents-cli update`; re-install them for this workspace with
`uvx google-agents-cli setup --workspace --agent claude-code`.

## Plan & Task Conventions

Plans and tasks for features are persisted at `.claude/plans/`.

### Folder structure

```
.claude/plans/
  {feature-slug}/
    plan.md                          # Architecture plan (architect)
    status.md                        # Progress tracker (architect creates, developer updates)
    tasks/
      TASK-001-{slug}.md             # One file per task (architect)
    walkthroughs/
      TASK-001-{slug}.md             # Implementation walkthrough (developer, auto-created)
```

### `status.md` lifecycle

| Status | Meaning |
|---|---|
| `⏳ pending` | Not yet started |
| `🔄 in-progress` | Claimed by a developer session (set before coding starts) |
| `✅ done` | Implementation complete, walkthrough exists |
| `❌ aborted` | Explicitly abandoned |

A task left at `🔄 in-progress` signals an interrupted session — the next developer agent must detect this and offer to resume.

### Naming conventions

- `{feature-slug}` — kebab-case of the feature name, e.g. `rag-tool-integration`
- `{NNN}` — zero-padded three-digit sequence, e.g. `001`, `002`
- Task filename — `TASK-{NNN}-{kebab-title}.md`
- Walkthrough filename — same pattern as the corresponding task file
