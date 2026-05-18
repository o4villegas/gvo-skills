# Local Patches Applied to Vendored Bundle

This file documents local fixes applied to the upstream vendor `awesome-claude-corporate-skills`. The fixes are necessary because:

1. The bundle ships SKILL.md files with broken / malformed frontmatter that prevents them from registering as skills (BAD_FRONTMATTER, MISSING_DESCRIPTION).
2. Several files have a `name:` field that doesn't match their directory (NAME_DIR_MISMATCH) — some intentional disambiguation, others unintentional.

Patched in this checkout on 2026-05-18 via [`scripts/fix-bundle.py`](../../scripts/fix-bundle.py). The script is idempotent — re-running on already-patched files is a no-op.

**If the bundle is re-vendored from upstream**, re-apply this manifest with `python3 scripts/fix-bundle.py` from the repo root. Preferred long-term fix: upstream the patches via a PR to <https://github.com/hesreallyhim/awesome-claude-corporate-skills> so the next vendor refresh carries them automatically.

---

## 28 files patched — BAD_FRONTMATTER → valid YAML frontmatter

Each file had its skill description living as a markdown paragraph under the H1 heading, instead of in a YAML frontmatter block. Patch: lift the body description into a proper `---\nname: <dir>\ndescription: >\n  <text>\n---\n` block.

All in `02-finance-accounting/`:

| File | Description chars |
|------|-------------------|
| `model-update/SKILL.md` | 402 |
| `deal-tracker/SKILL.md` | 396 |
| `teaser/SKILL.md` | 312 |
| `unit-economics/SKILL.md` | 444 |
| `dd-checklist/SKILL.md` | 437 |
| `client-report/SKILL.md` | 299 |
| `client-review/SKILL.md` | 389 |
| `deal-screening/SKILL.md` | 430 |
| `ic-memo/SKILL.md` | 402 |
| `dd-meeting-prep/SKILL.md` | 409 |
| `investment-proposal/SKILL.md` | 358 |
| `merger-model/SKILL.md` | 392 |
| `buyer-list/SKILL.md` | 403 |
| `earnings-preview/SKILL.md` | 380 |
| `cim-builder/SKILL.md` | 444 |
| `tax-loss-harvesting/SKILL.md` | 293 |
| `portfolio-monitoring/SKILL.md` | 440 |
| `catalyst-calendar/SKILL.md` | 358 |
| `idea-generation/SKILL.md` | 386 |
| `value-creation-plan/SKILL.md` | 453 |
| `sector-overview/SKILL.md` | 381 |
| `financial-plan/SKILL.md` | 354 |
| `thesis-tracker/SKILL.md` | 414 |
| `portfolio-rebalance/SKILL.md` | 289 |
| `morning-note/SKILL.md` | 324 |
| `process-letter/SKILL.md` | 321 |
| `returns-analysis/SKILL.md` | 387 |
| `deal-sourcing/SKILL.md` | 364 |

## 1 file patched — MISSING_DESCRIPTION → description added

Frontmatter was present but missing the `description:` field. Description was found as a body paragraph; lifted into frontmatter.

- `02-finance-accounting/check-model/SKILL.md` — 425-char description

## 8 files patched — NAME_DIR_MISMATCH → name field aligned with dir

Each file's `name:` field was different from its containing directory. Renamed the `name` field to match the dir (the dir is the user-facing identifier).

| File | Old name | New name |
|------|----------|----------|
| `02-finance-accounting/spglobal-earnings-preview/SKILL.md` | `earnings-preview-single` | `spglobal-earnings-preview` |
| `02-finance-accounting/spglobal-tear-sheet/SKILL.md` | `tear-sheet` | `spglobal-tear-sheet` |
| `02-finance-accounting/strip-profile/SKILL.md` | `fsi-strip-profile` | `strip-profile` |
| `02-finance-accounting/spglobal-funding-digest/SKILL.md` | `funding-digest` | `spglobal-funding-digest` |
| `02-finance-accounting/comps-analysis/SKILL.md` | `fsi-comps-analysis` | `comps-analysis` |
| `08-it-engineering/software-architecture/SKILL.md` | `ddd:software-architecture` | `software-architecture` |
| `07-operations/kaizen/SKILL.md` | `kaizen:kaizen` | `kaizen` |
| `03-human-resources/resume-generator/SKILL.md` | `tailored-resume-generator` | `resume-generator` |

## NOT patched — intentional disambiguators (validator allowlist instead)

These 4 files keep `name` shorter than dir on purpose. The dir suffix (`-common-room`, `-apollo`) disambiguates which platform-specific variant. `scripts/validate.py` was updated to allow `name + recognized-suffix == dir`.

- `05-sales/call-prep-common-room/SKILL.md` — `name: call-prep`
- `05-sales/prospect-common-room/SKILL.md` — `name: prospect`
- `05-sales/account-research-common-room/SKILL.md` — `name: account-research`
- `05-sales/prospect-apollo/SKILL.md` — `name: prospect`

---

## Pre-filled upstream issue body

If you want to file a PR upstream, here's a starting issue body. Copy to <https://github.com/hesreallyhim/awesome-claude-corporate-skills/issues/new>:

```markdown
Title: 37 SKILL.md files have malformed or mismatched frontmatter

Several SKILL.md files in the bundle currently fail standard skill-frontmatter validation. I have a one-shot patch script that fixes all of them; happy to submit as a PR.

**28 files in `02-finance-accounting/`** have their description as a body paragraph under the H1, with no YAML frontmatter at all. Files: model-update, deal-tracker, teaser, unit-economics, dd-checklist, client-report, client-review, deal-screening, ic-memo, dd-meeting-prep, investment-proposal, merger-model, buyer-list, earnings-preview, cim-builder, tax-loss-harvesting, portfolio-monitoring, catalyst-calendar, idea-generation, value-creation-plan, sector-overview, financial-plan, thesis-tracker, portfolio-rebalance, morning-note, process-letter, returns-analysis, deal-sourcing.

**1 file** (`02-finance-accounting/check-model/SKILL.md`) has frontmatter but is missing the `description:` field; the description is in the body.

**8 files** have a `name:` field that doesn't match the containing directory:
- 5 in `02-finance-accounting/`: spglobal-earnings-preview, spglobal-tear-sheet, strip-profile, spglobal-funding-digest, comps-analysis
- `08-it-engineering/software-architecture/SKILL.md` (name has invalid `:` character)
- `07-operations/kaizen/SKILL.md` (name has invalid `:` character)
- `03-human-resources/resume-generator/SKILL.md` (name has extra prefix)

For claude.ai cloud sessions, malformed frontmatter prevents the skill from registering at all. Without the patch, none of these 37 skills can be invoked.

I have a self-contained Python patcher that fixes all of them in ~1 second; happy to share or submit as a PR.
```
