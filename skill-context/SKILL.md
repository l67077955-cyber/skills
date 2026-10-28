---
name: skill-context
description: Audit and trim how much of Claude Code's context the skill listing uses. Inventories every skill by source (personal, claude.ai-synced, plugin, bundled) with its listing length, explains what each source can be switched with, and edits skillOverrides in ~/.claude/settings.json with a backup. Use when the user asks how much context skills take, why /context shows Skills at a round number, wants skills hidden from Claude but still callable with /name, wants to restore the default skill context, or asks whether a plugin, agent, or skill still costs context. Triggers include "優化 skill 上下文", "skill 佔多少上下文", "恢復默認上下文", "只用 / 調用", "skillOverrides".
---

# Skill context

Every skill's name and description sits in context on every turn; the SKILL.md body loads only when the skill is invoked (once per invocation, so `/html` loads html once, not twice). This skill measures that listing, shows what can be changed, and applies the user's choice. Reply in the user's language.

## Facts to work from

Checked against code.claude.com/docs (skills, settings-reference, sub-agents) on 2026-10-28. Re-fetch those pages if the user's Claude Code version looks much newer.

- **Budget.** The listing is capped at `skillListingBudgetFraction` of the context window (default 0.01). Over the cap, every name stays but the descriptions of the least-used skills are dropped. So a `/context` Skills row sitting on a round number (10.0k on a 1M window) means the listing is at the cap, and a skill shown with a bare name may just have been dropped. Cutting reduces the row only after the total falls below the cap.
- **Per-entry cap.** `description` + `when_to_use` are cut at `skillListingMaxDescChars` (default 1,536).
- **States** in `skillOverrides` (keys are skill names):

  | state | Claude sees | user can type `/name` |
  |---|---|---|
  | `on` (default, or absent) | name + description | yes |
  | `name-only` | name only | yes |
  | `user-invocable-only` | nothing | yes |
  | `off` | nothing | no, hidden |

- **Levers by source.**
  - Personal `~/.claude/skills/<name>` and project skills: `skillOverrides`, or `disable-model-invocation: true` in frontmatter. Confirmed. Prefer `skillOverrides`: it is one place to read and undo, and it leaves SKILL.md files alone. Skills installed from GitHub (impeccable, anatomy, design-taste-frontend, ...) get overwritten on update, so a frontmatter edit there silently disappears.
  - Bundled (dataviz, claude-api, code-review, loop, ...): `skillOverrides` per skill, or `disableBundledSkills: true` for all. Not on disk; count them from the skill listing in your own context.
  - claude.ai-synced (`anthropic-skills:*`, files in `~/.claude/skills/synced/`): turning the skill off in claude.ai settings is the confirmed way, and it applies on every device. `syncClaudeAiSkills: false` drops all of them on this machine. Whether `skillOverrides` works for them, and whether the key is the short or full name, is undocumented: say so, and verify in a new session.
  - Plugins (`plugin:skill`): `skillOverrides` does not apply. Only enable/disable/uninstall the whole plugin in `/plugin`; a disabled plugin's `/commands` disappear too, and its `.mcp.json` connectors go with it. The settings key is `enabledPlugins` (`{"<plugin>@<marketplace>": false}`); for a plugin synced from claude.ai the key has been observed as `<plugin>@synced`, which the docs don't confirm. So prefer telling the user to use `/plugin`; if you write the key, say it is unverified and how to check (`/reload-plugins` reports the plugin count). Synced plugins removed on claude.ai disappear at the next sync. To keep one plugin skill callable by `/` without the plugin, copy its folder into `~/.claude/skills/` (rename if it collides with a bundled name such as `debug` or `code-review`) and set it `user-invocable-only`.
- **Agents.** Built-in subagents (Explore, Plan, general-purpose, claude, statusline-setup, claude-code-guide) are defaults; their descriptions (~2.5k chars) are counted under System tools, not Skills. Custom ones live in `~/.claude/agents/`.
- Settings take effect in a **new session**. The listing in the current conversation never changes.

## Workflow

1. **Inventory.** Run `python3 <skill-dir>/scripts/skill_audit.py inventory`. It lists on-disk skills by source with full listing length and current override. Add the bundled skills by reading your own skill listing. Note any skill whose listing line lacks a description: compare with its SKILL.md to tell budget overflow from a genuinely empty description. If the script prints a frontmatter WARNING, pass it on to the user even when it is off-topic. Check your own listing before saying what it breaks: Claude Code's parser is more lenient than strict YAML (design-import kept its description in the listing despite failing strict parsing), so the concrete risk is strict tools such as `claude plugin validate`, not a missing description. Offer the fix; don't edit it unasked.
2. **Report** the total against the cap and the biggest contributors per source, with the lever for each. Mark numbers as estimates when they are char counts or proportional token splits rather than `/context` measurements.
3. **Agree on the plan with the user.** Don't pick what to hide on their behalf: usage is theirs to judge (`/skill-doctor` shows per-skill use; `~/.claude.json` → `pluginUsage` shows plugin use). Facts you can offer: skills whose tools don't exist in this environment, overlapping skills, and skills the system prompt requires (artifact-design and friends, claude-api) which should stay `on`.
   - This user's standing choice: everything else at the default, and their own `~/.claude/skills/` skills `user-invocable-only` (files stay where they are; they call them with `/`).
4. **Apply** with a dry run first, then `--write`:
   ```bash
   python3 <skill-dir>/scripts/skill_audit.py apply --personal user-invocable-only
   python3 <skill-dir>/scripts/skill_audit.py apply --personal user-invocable-only --write
   ```
   Other forms: `apply pptx=name-only dataviz=on`, `apply --remove xlsx`, `apply --reset --personal user-invocable-only` (back to defaults except personal skills). The script backs up to `~/.claude/backups/settings.json.bak-<time>` and leaves every other key alone. Never edit `env`, `permissions`, `model` or other keys as a side effect.
5. **List what only the user can do:** `/plugin` changes, claude.ai skill or connector settings.
6. **Verify** in a new session: the user checks the Skills row in `/context`, then asks you whether a given skill still has a description; you read your own listing to answer. If a synced-skill override had no effect, try the `anthropic-skills:<name>` key, then fall back to claude.ai settings.

If the user wants it drawn, build a page with before / now / after bars against the cap and one tile per skill showing its state.

## Adding third-party skills

When asked to install skills (for example `npx skills add <repo> --skill <name>`), first list what the repo actually offers (`npx -y skills add <repo> --list`): skills get merged or renamed, and a `--skill` that no longer exists installs nothing. Repos that ship per-agent copies may install a non-Claude variant (paths like `.agents/skills/...`); compare with the repo's `.claude/skills/<name>` and use that one. Read the SKILL.md and any launcher script before trusting it, note what it downloads and whether downloads are checksum-verified, and then set the new skill per the user's standing choice above. Warn that "pin"/shortcut features which create extra skills add listing entries.
