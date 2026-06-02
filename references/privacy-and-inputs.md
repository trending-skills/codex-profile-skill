# Privacy and Input Rules

Use this reference before publishing or rewriting a Codex profile.

## Source Types

Safe metadata sources:

- Codex thread state records
- Codex session index records
- Codex prompt-history record counts and aggregate keyword signals
- Codex rollout/session event records
- tool-call names and namespaces
- skill/plugin names exposed in safe metadata
- count-only ChatGPT conversation records

Do not copy raw prompts, raw message bodies, repository paths, project names, client names, private filenames, or private file contents into public output.

## User-Provided Publishing Inputs

Ask the user for these fields and treat them as optional:

- name
- location/timezone
- website URL
- GitHub URL or handle
- LinkedIn URL
- public email
- short bio
- final headline approval

If a contact field is missing, either hide the row or use a neutral placeholder such as `Add later`. Do not infer contact values from Git config, shell history, package metadata, browser data, local files, or previous private conversations.

## Public Wording

Prefer:

- `Codex metadata snapshot`
- `Codex state records`
- `session records`
- `prompt-history records`
- `aggregate activity snapshot`
- `ChatGPT conversation records were counted only as part of the broader activity snapshot.`

Avoid:

- `local metadata`
- `local machine`
- `binary contents`
- `not decoded`
- `not analyzed`
- direct filesystem paths

## Generated Copy

Headlines, summaries, operating style, current direction, workbench lists, language lists, and agent-stack groups may be generated from aggregate signals. Identity and contact details must be user-provided or explicitly confirmed.

When the analyzer emits `public_positioning.approval_required: true`, ask the user to approve or edit the selected headline before publishing.

## Link Rendering

Render provided contact values as clickable links:

- Website: normal `https://` URL
- GitHub: `https://github.com/<handle>` when only a handle is provided
- LinkedIn: full public profile URL
- Email: `mailto:` link

Validate obvious formatting issues, but do not invent missing values.
