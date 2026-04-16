---
name: full-stack-orchestration
description: >-
  9-step full-stack feature orchestrator with 3 phases, state persistence, and 
  specialist agent dispatch. Phase 1: Architecture (requirements, API design, DB schema). 
  Phase 2: Implementation (backend, frontend, tests with specialist agents). Phase 3: 
  Deployment (security audit, performance, deploy, docs). Use for end-to-end feature 
  builds spanning backend + frontend + database + tests + deployment.
version: 1.0.0
---

# Full-Stack Feature Orchestrator

End-to-end 9-step pipeline for full-stack feature development with specialist 
agent dispatch and state persistence.

## Pipeline

### Phase 1: Architecture & Design (Interactive)
1. Requirements gathering (Q&A)
2. API contract design  
3. Database schema design

### Phase 2: Implementation (Agent-Driven)
4. Backend implementation (specialist agent)
5. Frontend implementation (specialist agent)
6. Test suite (test-automator agent)

### Phase 3: Delivery (Automated)
7. Security audit (security-auditor agent)
8. Performance optimization (performance-engineer agent)
9. Deployment + documentation (deployment-engineer agent)

## State Persistence

Progress tracked in `.full-stack-feature/state.json` — resumable across sessions.

## Command

`/full-stack-feature <description> [--stack react/fastapi/postgres] [--complexity simple|medium|complex]`

See [commands/full-stack-feature.md](commands/full-stack-feature.md) for full protocol.
