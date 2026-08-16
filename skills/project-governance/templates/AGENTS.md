# {{PROJECT_NAME}} — Agent Onboarding Protocol

This file is the contract between the human and the AI agent for this project.
It is read at the start of every session. Do not modify it without human approval.

## Project Goal
{{PROJECT_GOAL}}

## Index Files & Reading Order
These files are the project's "map". Read them before any task.

| Index file | Purpose | When to read |
|---|---|---|
| `AGENTS.md` | This protocol | Every session |
| `index.md` | Authoritative directory map | Every session, before finding any file |
| `session_handoff.md` | Last session's progress & open questions | Every session |
| `LESSONS.md` | Historical AI errors & corrections | Every session |
| `blacklist.json` | Failed parameters (permanent bans) | Before generating any parameters |
| `whitelist.json` | Verified parameters (preferred baselines) | Before generating any parameters |
| `VERSIONS.md` | Stable version index with human judgments | When choosing or reviewing versions |
| `CHANGELOG.md` | Version history of decisions | When reviewing history |

## Directory Permission Zones
- 🔴 **Core spec zone** — never modify: protocol files, specs, indexes.
- 🟡 **Core code zone** — explain impact and wait for confirmation before modifying.
- 🟢 **Agent workspace** — free to create/edit.
- 📂 **Reference / assets** — read-only.
- 🗑️ **Archived** — read-only; never use as current authority.

## Artifact Placement Rules
1. Never create new files at the project root (except spec files).
2. Never write directly into reference/asset zones.
3. All generated artifacts go into the designated workspace/output folders.
4. Naming convention: `[type]_[date]_[version]_[description]`.

## Autonomy Levels
- **Level 0 (read-only)**: analyze, explain, generate reports.
- **Level 1 (workspace)**: may modify workspace files.
- **Level 2 (core code)**: must explain impact and wait for confirmation before modifying core code.
- **Level 3 (forbidden)**: spec files, reference zones — never modify.

## Index-First File Lookup
To find any file / directory / version:
1. Read `index.md` (the only authoritative map).
2. Open the target file the index points to.
3. If the index does not list the target, infer by naming convention but confirm existence with the human.
4. If the index points to a migrated/archived file, stop and report.

Never search the filesystem by blind keyword/glob before reading the index.

## Session Handoff
At the end of every session, update `session_handoff.md` with: what was done, what is pending, open questions, next steps.

## Lessons Recording
1. If a task resembles a historical error in `LESSONS.md`, stop and report immediately.
2. If a new mistake is made, append an entry: date + error + root cause + correction + lesson.
3. Never record an error without its correction.
4. Modifying `LESSONS.md` requires explaining the change and waiting for human confirmation.

## Parameter Registry Rules
1. Before generating any new parameters, read `blacklist.json` and `whitelist.json`.
2. Never use `permanent_ban: true` entries.
3. Prefer inheriting `whitelist` entries with `score > 0.85` as the baseline, then fine-tune.
4. Record new verified/failed parameters back into the registries after testing.
5. Mark replaced entries with `superseded_by` instead of deleting them.
