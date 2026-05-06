# gvo-skills/scripts

Maintenance scripts for the gvo-skills repo.

## sync-bundle-registry.py

Adds skills from a third-party bundle (typically a downloaded GitHub
release) into `skills/nexus/registry.json` so `/nexus` can surface them
through trigger matching.

**Curation is a human step.** The script automates inventory, collision
checks against the existing nexus registry and the harness's plugin
skills, and the boilerplate of generating ids/paths. You still pick
which skills to keep and write triggers for each — without triggers
nexus will not match the skill against user phrasing.

### Three-step workflow

```bash
# 1. Audit — see what's in the bundle and what collides
python scripts/sync-bundle-registry.py audit skills/<bundle> --verbose

# 2. Stub — write skeleton entries for the net-new candidates
python scripts/sync-bundle-registry.py stub skills/<bundle> --out candidates.json

# 3. (Edit candidates.json by hand: drop entries you don't want, set
#     category, write triggers for each one you keep.)

# 4. Apply — append the curated entries to registry.json
python scripts/sync-bundle-registry.py apply candidates.json
```

### When to update PLUGIN_SKILLS

The plugin-skills list in the script is hardcoded from the harness's
available-skills section. When Anthropic ships new plugin skills, add
their names to that set so they don't get re-imported as duplicates
from a future bundle.

### Path resolution

Generated `path` fields are relative to `skills/nexus/`:
- For bundles inside `skills/`: `../<bundle>/<...>/SKILL.md`
- For sibling top-level skills: `../<name>/SKILL.md`
- For nested skills inside nexus: `skills/<name>/SKILL.md`

If the bundle lives outside `skills/`, the stub uses an absolute path
and you'll need to fix it manually before `apply`.
