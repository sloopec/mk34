# ADK Knowledge Provider

Provides Google ADK (Agent Development Kit) reference knowledge for architects and developers. Covers core concepts, patterns, API primitives, and project-specific conventions.

## When to use

- You need to look up ADK concepts, primitives, or patterns
- You need project-specific ADK conventions (Nexus proxy, LLM wrappers, session management)
- Trigger phrases: "ADK reference", "how does ADK handle…", "ADK best practice for…"

## Knowledge Base

Read the file `.github/skills/adk-knowledge-provider/ADK_KNOWLEDGE.md` for the full reference material. If the file cannot be read, state explicitly that project-specific conventions are unavailable and rely solely on retrieved official documentation.

When answering questions:
1. Use `mcp__context7__resolve-library-id` with `google-adk` (or the relevant library name) to get the library ID, then call `mcp__context7__query-docs` with that ID to retrieve the latest official documentation. If the MCP tool calls fail or return no results, skip to step 2 and note that official documentation could not be retrieved.
2. Read `.github/skills/adk-knowledge-provider/ADK_KNOWLEDGE.md` to ground your response in project-specific patterns and conventions.
3. Cite specific sections or components from both sources. If the two sources conflict, prefer `ADK_KNOWLEDGE.md` for project-specific conventions and the official documentation for general API behavior. Always note the discrepancy explicitly.
4. If neither source covers the topic, respond with: "This topic is not covered in the project knowledge base or the retrieved documentation. The following is based on general reasoning and may not reflect current ADK behavior or project conventions:" then provide the best-effort answer.

## Plan & Task Conventions

Plans and tasks for features are persisted at `.github/plans/`.

### Folder structure

```
.github/plans/
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
