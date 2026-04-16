# Nexus Repo Scan Results — April 13, 2026

## Inventory Summary

| Repo | Total SKILL.md | High-Value for Nexus | Action |
|------|---------------|---------------------|--------|
| agentsys | 30 | 8 | Extract patterns + select skills |
| claw-code | 0 | 0 | Reference only (Rust Claude Code alt) |
| everything-claude-code | 183 unique | 12 | Cherry-pick best skills |
| slavingia/skills | 10 | 3 | Business/startup skills for GVO |
| claude-skills | 239 primary | 8 | Selective — marketing, finance, engineering bundles |
| OpenSpace | 264 | 2 | Already extracted to skill-evolution Worker spec |
| **TOTAL** | **726 unique** | **33 candidates** | |

---

## Tier 1: Direct Pipeline Integration (Install into nexus/skills/)

These skills map directly to Nexus pipeline phases and should be installed.

### From agentsys

| Skill | Maps To | Why |
|-------|---------|-----|
| `debate` | Phase 3 (Plan) | Structured multi-round adversarial debate between AI tools. Evidence-based argumentation with verdicts. Adapts perfectly to the expert roundtable. |
| `consult` | Phase 3 (Plan) | Cross-tool AI consultation (Claude, Gemini, Codex, Copilot, OpenCode). Enables getting second opinions from different models during planning. |
| `orchestrate-review` | Phase 5 (Implementation) | Multi-pass parallel code review — code quality, security, performance, test coverage + conditional specialists (DB, API, frontend, backend, devops). Iteration loop with stall detection. |
| `validate-delivery` | Phase 7 (Final Delivery) | Autonomous delivery validation — tests, build, requirements check, regression detection. Structured pass/fail with fix instructions. |
| `deslop` | Phase 5 (Implementation) | AI slop detection and auto-fix. HIGH/MEDIUM/LOW certainty levels. Debug statements, placeholder text, dead code, orphaned infrastructure. |
| `repo-intel` | Phase 2 (Domain Check) | Git history intelligence + AST symbol mapping. Hotspots, ownership, bus factor analysis. Enhances domain understanding of existing codebases. |

### From everything-claude-code

| Skill | Maps To | Why |
|-------|---------|-----|
| `council` | Phase 3 (Plan) | Four-voice decision council (Architect, Skeptic, Pragmatist, Critic). Anti-anchoring via independent subagents. Structured verdict format. Directly replaces ad-hoc "perspective-taking." |
| `blueprint` | Phase 3 (Plan) | Construction plan generator for multi-session projects. 5-phase pipeline: Research → Design → Draft → Review → Register. Self-contained context briefs per step. |
| `verification-loop` | Phase 5/7 | Build → Type Check → Lint → Test → Security Scan → Diff Review. Structured verification report. Continuous mode for long sessions. |
| `agentic-engineering` | Core Philosophy | Eval-first execution, 15-minute task decomposition, model tier routing (Haiku/Sonnet/Opus). Cost discipline. Core operating principles for the entire pipeline. |
| `search-first` | Phase 2 (Domain Check) | Search existing codebase before writing new code. Pattern: grep, find, read before create. |
| `continuous-agent-loop` | Phase 5 (Implementation) | Autonomous agent loops with checkpoints. Build → verify → iterate without user intervention. |

---

## Tier 2: Valuable Reference Patterns (Extract to nexus/references/)

### From agentsys

| Skill | Extract As | Value |
|-------|-----------|-------|
| `drift-analysis` | references/drift-detection.md | Code drift detection between documentation and implementation |
| `enhance-prompts` | references/prompt-enhancement.md | Patterns for improving prompt quality |
| `enhance-skills` | references/skill-improvement.md | Patterns for improving skill quality (feeds into evolution engine) |
| `learn` | references/learning-patterns.md | How agents learn from mistakes |
| `discover-tasks` | references/task-discovery.md | Autonomous task identification in codebases |

### From everything-claude-code

| Skill | Extract As | Value |
|-------|-----------|-------|
| `coding-standards` | references/coding-standards.md | Universal coding standards for agent-generated code |
| `mcp-server-patterns` | references/mcp-patterns.md | MCP server design patterns (relevant for from-desktop, skill-evolution) |
| `deployment-patterns` | references/deployment-patterns.md | Deployment automation (CF Workers already well-known, but still useful) |
| `tdd-workflow` | references/tdd-patterns.md | Test-driven development patterns for Claude Code |
| `e2e-testing` | references/e2e-testing.md | Playwright/e2e test patterns |
| `security-review` | references/security-checklist.md | Security review checklist for agent-generated code |

---

## Tier 3: Domain Skills — On-Demand Loading

### From slavingia/skills (Business/Startup)

| Skill | Category | Relevance |
|-------|----------|-----------|
| `validate-idea` | business | GVO business validation |
| `mvp` | business | MVP planning for new GVO products |
| `pricing` | business | Pricing strategy (KC Clearwater, GVO services) |
| `marketing-plan` | business | Marketing for Moonlit Frequencies, KC, GVO |
| `first-customers` | business | Customer acquisition |
| `grow-sustainably` | business | Growth strategy |

### From claude-skills (Selected High-Value)

| Skill | Category | Relevance |
|-------|----------|-----------|
| `autoresearch-agent` | engineering | Autonomous research loops (enhances from-prompter) |
| `karpathy-coder` | engineering | Karpathy-style methodical coding |
| `focused-fix` | engineering | Focused bug fixing (Phase 5 quick-fix path) |
| `financial-analyst` | finance | Financial analysis (enhances KC Pulse work) |
| `saas-metrics-coach` | finance | SaaS metrics for GVO products |
| `product-manager-toolkit` | product | Product management for feature planning |
| `senior-architect` | engineering | Architecture review patterns |
| `startup-cto` | strategy | CTO-level strategic thinking for GVO |

---

## Tier 4: Skip (Not Relevant to Lando's Stack/Workflow)

| Category | Count | Reason |
|----------|-------|--------|
| Language-specific (Go, Rust, Python, Swift, Kotlin, Java, C++, Perl, etc.) | ~80 | Lando's stack is TypeScript/JavaScript exclusively |
| Framework-specific (Django, Laravel, Spring Boot, NestJS, Flutter, etc.) | ~40 | Not in Lando's stack |
| Enterprise ops (Jira, Confluence, Atlassian, Terraform, Helm, K8s) | ~25 | Not Lando's ops model |
| Healthcare/regulatory (HIPAA, FDA, MDR, ISO 13485) | ~15 | Not relevant |
| Supply chain/logistics | ~10 | Not relevant |
| Crypto/DeFi | ~5 | Not relevant |
| Translations (zh-CN, ko-KR, zh-TW, tr, ja-JP copies) | ~200 | Duplicates of English originals |
| OpenSpace benchmark skills (gdpval_bench) | ~200 | Test/benchmark artifacts, not production skills |

---

## Extraction Commands

### Install Tier 1 Skills

```bash
NEXUS="/home/lando555/.claude/skills/nexus/skills"

# From agentsys
for skill in debate consult orchestrate-review validate-delivery deslop repo-intel; do
  mkdir -p "$NEXUS/$skill"
  cp "/home/lando555/agentsys/.kiro/skills/$skill/SKILL.md" "$NEXUS/$skill/"
  echo "Installed: $skill (agentsys)"
done

# From everything-claude-code
for skill in council blueprint verification-loop agentic-engineering search-first continuous-agent-loop; do
  mkdir -p "$NEXUS/$skill"
  cp "/home/lando555/everything-claude-code/skills/$skill/SKILL.md" "$NEXUS/$skill/"
  echo "Installed: $skill (everything-claude-code)"
done
```

### Extract Tier 2 References

```bash
REFS="/home/lando555/.claude/skills/nexus/references"

# From agentsys
for skill in drift-analysis enhance-prompts enhance-skills learn discover-tasks; do
  cp "/home/lando555/agentsys/.kiro/skills/$skill/SKILL.md" \
     "$REFS/${skill}.md"
  echo "Extracted: $skill → references/"
done

# From everything-claude-code
for skill in coding-standards mcp-server-patterns deployment-patterns tdd-workflow e2e-testing security-review; do
  cp "/home/lando555/everything-claude-code/skills/$skill/SKILL.md" \
     "$REFS/${skill}.md"
  echo "Extracted: $skill → references/"
done
```

### Install Tier 3 Domain Skills

```bash
# Slavingia business skills
for skill in validate-idea mvp pricing marketing-plan first-customers grow-sustainably; do
  mkdir -p "$NEXUS/$skill"
  cp "/home/lando555/skills/skills/$skill/SKILL.md" "$NEXUS/$skill/"
  echo "Installed: $skill (slavingia)"
done

# Claude-skills selected
for skill in autoresearch-agent karpathy-coder focused-fix; do
  mkdir -p "$NEXUS/$skill"
  cp "/home/lando555/claude-skills/engineering/$skill/SKILL.md" "$NEXUS/$skill/"
  echo "Installed: $skill (claude-skills)"
done
```

---

## Key Architectural Insight

After scanning all 726 skills, the Nexus pipeline phases map perfectly to existing battle-tested skills:

| Phase | Primary Skill | Secondary | Source |
|-------|--------------|-----------|--------|
| 1. Interview | nexus SKILL.md (built-in) | — | Custom |
| 2. Domain Check | `repo-intel` + `search-first` | from-desktop, web search | agentsys + ECC |
| 3. Plan Development | `council` + `blueprint` | `debate` (for contentious decisions) | ECC + agentsys |
| 4. Approval | nexus SKILL.md (built-in) | — | Custom |
| 5. Implementation | `orchestrate-review` + `deslop` + `verification-loop` | `continuous-agent-loop` | agentsys + ECC |
| 6. Pre-Delivery | `ux-diagnostic` + `verification-loop` | — | Existing + ECC |
| 7. Final Delivery | `validate-delivery` | — | agentsys |

This means the Nexus pipeline doesn't need to be built from scratch — it's an orchestration layer over proven, battle-tested skills from the best open-source repositories.
