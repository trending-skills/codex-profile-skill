---
name: codex-profile
description: Create public-safe AI collaboration profile sites from Codex metadata. Use when the user wants to analyze Codex activity, generate an AI work profile, package a reusable profile site, calculate workbench/tool/language signals, add public-safe evidence wording, collect user-approved identity/contact fields, or generate Open Graph/social preview images for the profile.
---

# Codex Profile

Create a publishable static AI collaboration profile from aggregate Codex metadata plus user-approved public identity fields. The output should feel like a modern AI-work profile, not a traditional resume.

## Workflow

1. Read `references/privacy-and-inputs.md` before publishing, rewriting evidence text, or handling contact fields.
2. Ask the user for public identity/contact fields when they are needed:
   - name
   - location/timezone
   - website URL
   - GitHub URL or handle
   - LinkedIn URL
   - public email
   - optional short bio
3. Treat those fields as user-provided publishing inputs. Do not infer or publish contact details from local files, shell history, Git config, browser data, or private metadata unless the user explicitly confirms each value.
4. Run `scripts/analyze_codex_activity.py` when Codex metadata is available and the user wants calculated metrics.
5. Use `assets/profile-template/public-inputs.example.json` to shape user-provided publishing fields.
6. Use `assets/profile-template/index.html` and `assets/profile-template/social-preview.html` as the starting templates.
7. Replace template identity, contact, headline, metrics, workbench, agent stack, language, evidence, and preview content with the analyzed data and user-approved public fields.
8. Ask the user to approve or edit generated positioning/headline copy before publishing.
9. Generate `social-preview.png` with `scripts/generate_social_preview.mjs` when Playwright is available.
10. Verify the page for privacy, layout, links, metadata, and social image dimensions before final handoff.

## Data Boundaries

Metadata-derived sections may include:

- aggregate activity counts
- work mix
- action mix
- AI Workbench tools
- agent/plugin stack signals
- programming language signals
- operating style
- current direction
- headline candidates from aggregate labels

User-provided sections must include:

- identity
- location/timezone
- public contact links
- email
- optional bio or final public headline approval

Never publish:

- raw prompts
- repository paths
- filesystem paths
- project/client/company names from private metadata
- private file contents
- decoded ChatGPT conversation content unless explicitly exported and approved

## Scripts

Run the analyzer from the output project root:

```bash
python3 path/to/skill/codex-profile/scripts/analyze_codex_activity.py
```

Useful environment variables:

- `CODEX_HOME`: Codex data directory. Defaults to `~/.codex`.
- `CHATGPT_CONVERSATIONS_DIR`: optional local ChatGPT conversation storage directory for count-only blob totals.
- `OUTPUT_PATH`: output JSON path. Defaults to `data/profile_analysis.json`.

Generate the social preview image from the output project root:

```bash
node path/to/skill/codex-profile/scripts/generate_social_preview.mjs social-preview.html social-preview.png
```

If Playwright is installed outside the project:

```bash
PLAYWRIGHT_MODULE_PATH=/path/to/node_modules/playwright node path/to/skill/codex-profile/scripts/generate_social_preview.mjs social-preview.html social-preview.png
```

## Template Use

Copy the files from `assets/profile-template/` into the output project, then edit them for the target profile. Keep the inline SVG icons and local CSS so the output works without a CDN, package install, or account-specific asset path.

Minimum output files:

- `index.html`
- `social-preview.html`
- `social-preview.png` if image generation is available
- `public-inputs.json` or equivalent documented user-provided fields
- `data/profile_analysis.json` or a documented equivalent if calculated metrics are used

Prefer public wording such as:

- `Codex metadata snapshot`
- `Codex state records`
- `session records`
- `prompt-history records`
- `ChatGPT conversation records were counted only as part of the broader activity snapshot.`

Avoid public wording such as:

- `local metadata`
- `local machine`
- `binary contents were not analyzed`
- direct filesystem locations

## Verification

Before final handoff:

1. Inspect the rendered page at desktop and mobile widths.
2. Confirm no horizontal overflow, clipping, broken icons, or broken theme toggle.
3. Confirm all provided contact rows are real clickable links.
4. Hide or neutralize missing contact rows; do not invent links.
5. Confirm Open Graph/Twitter tags point to an existing `social-preview.png`.
6. Confirm the social image is 1200 by 630.
7. Search the final HTML for forbidden private terms and filesystem paths.

Use Playwright or the Browser plugin for rendered checks when available.
