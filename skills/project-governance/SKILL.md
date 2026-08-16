---
name: project-governance
description: Set up and maintain a project governance workspace for AI-assisted development — a project protocol (rules, permissions, autonomy levels), directory index, lessons log, session handoff, changelog, and a whitelist/blacklist decision registry. Use when starting a new AI-assisted project, onboarding an AI agent into an existing project, or when a project lacks structured rules, error archives, or parameter versioning.
---

# Project Governance

## Description

A lightweight, agent-readable governance layer for AI-assisted projects. It turns implicit working conventions into explicit, versioned files that both humans and AI agents follow, so long-running agent work stays consistent, auditable, and reproducible across sessions.

The workspace produced by this skill contains:

| File | Purpose |
|---|---|
| `AGENTS.md` | Project protocol: goals, index files, directory permission zones, autonomy levels, artifact placement rules, index-first lookup, handoff & lessons discipline |
| `ARCHITECTURE.md` | System architecture: components, data interfaces, conventions, terminology |
| `PROJECT.md` | One-page project card: goal, status, deliverables |
| `index.md` | Authoritative directory map, updated on every file add/remove/move |
| `LESSONS.md` | AI error & correction log (phenomenon → root cause → correction → lesson) |
| `session_handoff.md` | End-of-session handoff so the next session resumes cleanly |
| `CHANGELOG.md` | Version history of decisions and outcomes |
| `VERSIONS.md` | Stable version index with human judgments and evidence links |
| `blacklist.json` | Registry of failed parameters/approaches (permanent bans) |
| `whitelist.json` | Registry of verified-good parameters/approaches (preferred baselines) |

## When to Use

Use this skill when:

- Starting a new AI-assisted project and you want the agent to follow a stable protocol from day one.
- Onboarding an AI agent into an existing project that has no rules, error log, or parameter registry.
- A project has grown messy: files scattered, parameters changed without record, past mistakes repeated.
- You want to enforce durable rules such as "index-first file lookup", "plan before execute", or "registry-driven parameter selection".

Do NOT use this skill when:

- The task is a one-off question or small edit that does not need project-wide conventions.
- The project already has a mature governance system and you only need a small rule tweak — edit the existing files directly instead.

## Workflow

### Step 1 — Scaffold the governance workspace

Run the scaffold script:

```bash
python scripts/governance.py init --project-dir /path/to/project --project-name "My Project"
```

This creates `AGENTS.md`, `ARCHITECTURE.md`, `PROJECT.md`, `index.md`, `LESSONS.md`, `session_handoff.md`, `CHANGELOG.md`, `VERSIONS.md`, `blacklist.json`, and `whitelist.json` from `templates/`. It never overwrites existing files unless `--force` is passed.

Alternatively, copy the files from `templates/` manually and fill in the `{{PLACEHOLDER}}` values.

### Step 2 — Customize the protocol

Edit `AGENTS.md` to reflect the project's real constraints:

- Directory permission zones (which areas are read-only / require confirmation / free to edit).
- Autonomy levels (what the agent may do without asking).
- Artifact placement rules (where generated files must go).
- Index files and their reading order.

### Step 3 — Maintain the workspace

Every session, follow this loop:

1. **On session start**: read `index.md` → `session_handoff.md` → `LESSONS.md` (and `blacklist.json`/`whitelist.json` before any parameter generation).
2. **During work**:
   - Find files via the index, never by blind keyword search.
   - Before generating parameters, read `blacklist.json` and `whitelist.json`; inherit from `whitelist` entries with `score > 0.85`; never use `permanent_ban: true` entries.
   - Record any new mistake in `LESSONS.md` (phenomenon → root cause → correction → lesson).
3. **On session end**: update `session_handoff.md` with progress, open questions, and next steps; update `index.md` for any file changes; append to `CHANGELOG.md`.

### Step 4 — Validate the registries

```bash
python scripts/governance.py validate --project-dir /path/to/project
```

Checks that `blacklist.json` and `whitelist.json` conform to the schema (required fields, valid `status`/`judge` values, unique `id`s).

### Step 5 — Refresh the directory index

```bash
python scripts/governance.py index --project-dir /path/to/project
```

Rebuilds the `Root layout` section of `index.md` from a filesystem scan, so the
map stays in sync with the actual directory structure.

## File Reference

- `templates/AGENTS.md` — protocol template
- `templates/ARCHITECTURE.md` — architecture template
- `templates/PROJECT.md` — project card template
- `templates/index.md` — directory map template
- `templates/LESSONS.md` — error log template
- `templates/session_handoff.md` — handoff template
- `templates/CHANGELOG.md` — changelog template
- `templates/VERSIONS.md` — stable version index template
- `templates/blacklist.json` — failed-parameter registry schema
- `templates/whitelist.json` — verified-parameter registry schema
- `scripts/governance.py` — scaffold + validate + index CLI
- `tests/test_governance.py` — 60-case robustness/boundary suite incl. adversarial inputs (stdlib-only)
- `examples/example-workflow.md` — end-to-end walkthrough

## Best Practices

- Keep `AGENTS.md` concise; put details in referenced files.
- Distinguish AI review from human review in `CHANGELOG.md` and registry entries (`judge` field). Human review is authoritative.
- Use `superseded_by` to mark registry entries that have been replaced instead of deleting them.
- Prefer deterministic outputs: templates, checklists, structured JSON.
- Keep registry entries small and specific; one failed parameter per entry.
