---
name: skill-evolution
description: >
  Skill evolution Worker API client. Use to record task analyses, evolve skills
  (fix/derived/captured), register new skills, check health, or view the
  dashboard. Trigger on: "record analysis", "evolve skill", "fix skill",
  "derive skill", "capture skill", "skill health", "register skill",
  "skill-evolution", "skill dashboard", "skill performance".
---

# Skill Evolution — Worker API

The skill-evolution Worker (`/home/lando555/skill-evolution/`) stores a D1-backed
history of every skill and records task-level judgments of how each skill performed.

Deployed at **`https://skill-evolution.lando555.workers.dev`**.

Repo is **standalone** — do NOT merge into nexus or any other project.

---

## When to use this skill

| Trigger | Endpoint |
|---------|----------|
| Phase 7 delivery — record skill performance | `POST /analyses` |
| Fix a typo / tighten a rule in an existing skill | `POST /evolve/fix` |
| Build a new variant based on a parent skill | `POST /evolve/derived` |
| Capture a brand-new skill from the session | `POST /evolve/captured` |
| Seed a skill the Worker doesn't know yet | `POST /skills/register` |
| "What skills do I have?" | `GET /skills` |
| "Show me skill health" / "skill dashboard" | `GET /dashboard` |
| Debug: is the Worker up? | `GET /health` |

---

## Data model (append-only)

Every skill lives as a row in `skill_records`. Evolves create **new rows**, never mutate. Old versions stay readable forever.

- `id`: `{name}__imp_{random8hex}`
- `name`: logical name (e.g. `"council"`)
- `version`: integer, bumps per evolve
- `isActive`: `true` for the current head, `false` for old versions
- `parentId`: FK to previous row (null for originals / captured)
- Content + SHA-256 hash for diff detection

Lineage edges (`skill_lineage_parents`) carry `relation: "evolved" | "derived" | "captured" | "forked"`.

Rollback = flip `isActive` on the desired row (via direct D1 query for now; `/rollback` route pending).

---

## Endpoint reference

### `GET /health`
```json
{ "status": "ok", "service": "skill-evolution", "version": "0.1.0", "timestamp": "..." }
```

### `GET /dashboard`
Server-rendered HTML. Midnight glass aesthetic. Shows active-skill count, total records, recent analyses, and a skills table.

### `POST /skills/register`
Seed a skill. Idempotent by `(name, content_hash)`.
```json
{
  "name": "council",
  "description": "Four-voice planning pattern...",
  "content": "---\nname: council\n...",
  "source": "everything-claude-code",
  "category": "planning"
}
```
Returns `{ skill, created: true|false }`.

### `GET /skills[?category=planning]`
List all active skill heads. Optional category filter.

### `GET /skills/:name`
Current active version. 404 if missing.

### `GET /skills/:name/history`
Full version chain, newest first.

### `POST /analyses`
Record a task-level analysis. Call this at Phase 7 final delivery after every Nexus task.
```json
{
  "taskId": "uuid-or-slug",
  "taskCompleted": true,
  "note": "optional",
  "skillJudgments": [
    { "skillId": "council", "skillApplied": true, "note": "Used for Phase 3" },
    { "skillId": "ux-diagnostic", "skillApplied": false, "note": "No UI surface" }
  ]
}
```
Atomic via `db.batch()` — the analysis and all its judgments land together or not at all.

### `GET /analyses[?limit=50]` / `GET /analyses/:id`
List recent analyses / fetch one with its judgments.

### `POST /evolve/fix`
**Corrective edit to an existing skill.** Same `name`, new row with `parent_id = current head`, `version+1`. Old head flipped `is_active=false`. Lineage edge `"evolved"`.
```json
{ "name": "council", "description": "...", "content": "..." }
```
Returns 404 if no active skill with that name, or `{ created: false, reason: "content unchanged" }` if the hash matches.

### `POST /evolve/derived`
**New skill inspired by an existing parent.** NEW `name`, new row with `parent_id = source skill`, `version=1`. Parent stays active. Lineage edge `"derived"`. Name collisions → 409.
```json
{ "name": "council-quick", "parentName": "council", "description": "...", "content": "..." }
```

### `POST /evolve/captured`
**Brand-new skill with no parent.** Use for skills extracted from a session that don't derive from anything. No lineage row. Name collisions → 409.
```json
{ "name": "my-new-skill", "description": "...", "content": "..." }
```

---

## Failure modes

| Failure | UI handling |
|---------|-------------|
| Worker down / 500 | Phase 7 delivery skips recording silently (already documented in pipeline/07-final-delivery.md). Nexus itself does NOT depend on the Worker for orchestration. |
| D1 migration drift | `wrangler d1 migrations apply skill-evolution --remote` from the `/home/lando555/skill-evolution/` repo |
| Deploy broken | `wrangler deploy` from the repo, or `git push` if Git integration is wired |

---

## Auth

None in v1. Single-user Worker. Public URL. If you need auth later, add an HMAC-signed `X-Nexus-Token` header via Hono middleware (see kc-cogs `middleware/auth.ts` for the canonical pattern).

---

## Client usage from Nexus

From any Nexus pipeline phase, use `curl` via Bash or `WebFetch`:

```bash
curl -X POST https://skill-evolution.lando555.workers.dev/analyses \
  -H "Content-Type: application/json" \
  -d '{"taskId":"<uuid>","taskCompleted":true,"skillJudgments":[...]}'
```

No SDK. The API is 6 endpoints; direct HTTP is clearer than wrapping them.
