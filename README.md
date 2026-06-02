# Codex Profile Skill

Create public-safe AI collaboration profile sites from aggregate Codex metadata.

`codex-profile` is a reusable Codex skill for turning local Codex activity signals into a publishable static profile page. It is designed for builders, maintainers, and teams who want to show AI-assisted engineering work without exposing private prompts, repository paths, project names, client names, or file contents.

## What It Generates

- A static AI collaboration profile page
- Aggregate activity and work-mix sections
- Metadata-derived AI Workbench, agent stack, and language signals
- Public-safe evidence/source wording
- User-approved identity and contact fields
- A 1200 by 630 social preview image template

## Repository Layout

```text
SKILL.md
agents/openai.yaml
references/privacy-and-inputs.md
scripts/analyze_codex_activity.py
scripts/generate_social_preview.mjs
assets/profile-template/
```

## Privacy Model

The skill separates calculated metadata from user-provided publishing fields.

Metadata-derived sections may include:

- aggregate activity counts
- work mix and action mix
- AI Workbench tools
- agent/plugin stack signals
- programming language signals
- operating style
- current direction
- headline candidates from aggregate labels

User-provided fields include:

- name
- location/timezone
- website URL
- GitHub URL or handle
- LinkedIn URL
- public email
- final headline approval

The skill should not publish raw prompts, repository paths, filesystem paths, private project names, client names, private file contents, or decoded ChatGPT conversation content unless explicitly exported and approved.

## Install

Copy this repository into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/trending-skills/codex-profile-skill.git ~/.codex/skills/codex-profile
```

Then start a fresh Codex thread and ask:

```text
Use $codex-profile to create a public-safe AI collaboration profile from Codex metadata.
```

## Use The Analyzer

Run from the profile project you want to generate:

```bash
python3 ~/.codex/skills/codex-profile/scripts/analyze_codex_activity.py
```

Useful environment variables:

- `CODEX_HOME`: Codex data directory. Defaults to `~/.codex`.
- `CHATGPT_CONVERSATIONS_DIR`: optional local ChatGPT conversation storage directory for count-only totals.
- `OUTPUT_PATH`: output JSON path. Defaults to `data/profile_analysis.json`.

The analyzer emits aggregate counts, keyword scores, tool/language/plugin signals, and public positioning candidates. It does not copy raw prompts, repository paths, or file contents into the output.

## Use The Templates

Starter files live in:

```text
assets/profile-template/
```

The template includes:

- `index.html`
- `social-preview.html`
- `public-inputs.example.json`
- `profile_analysis.example.json`

`public-inputs.example.json` uses placeholders. Replace those with user-approved public identity/contact fields before publishing.

## Generate Social Preview

The social preview image is generated from editable HTML/CSS.

```bash
node ~/.codex/skills/codex-profile/scripts/generate_social_preview.mjs social-preview.html social-preview.png
```

If Playwright is installed outside the project:

```bash
PLAYWRIGHT_MODULE_PATH=/path/to/node_modules/playwright node ~/.codex/skills/codex-profile/scripts/generate_social_preview.mjs social-preview.html social-preview.png
```

## Verification Checklist

Before publishing a generated profile:

- Confirm contact links are user-provided and clickable.
- Confirm missing contact rows are hidden or clearly marked as placeholders.
- Confirm Open Graph/Twitter image tags point to `social-preview.png`.
- Confirm the social image is 1200 by 630.
- Inspect desktop and mobile render.
- Search final HTML for raw prompts, filesystem paths, local usernames, private project names, and private file contents.

## Status

This is an early reusable skill. The current version includes the workflow, privacy reference, analyzer, social-preview exporter, and static templates. A future improvement would add a deterministic renderer that converts `profile_analysis.json` plus `public-inputs.json` directly into `index.html` and `social-preview.html`.
