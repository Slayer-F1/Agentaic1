# مُنجِز — Munjiz

Entry for the **AI Agents Innovation Challenge** (تحدي ابتكار وكلاء الذكاء الاصطناعي): **one** generic AI agent that completes all routine employee/government transactions conversationally — governed by **skills-as-code**.

Every procedure is a versioned, approved `SKILL.md` in this repo (fields, eligibility rules, allowed services, approval chain, escalation) + a `PROFILE.md` persona. The n8n agent loads the matching skill **live from GitHub** per request, becomes that procedure's expert, and every data/tool call passes a **service gateway** that enforces the skill's allowlist and writes an audit row — including denials. Adding a new procedure = pushing one markdown file. Zero n8n changes.

Built on **n8n + Google Gemini 2.5 Flash (free tier)**, Google Sheets as the transactional registry, and a bilingual RTL chat-first portal.

## Repository map

| Path | Contents |
|---|---|
| `skills/` | The governed skill library (leave, salary certificate, expense claim, IT access) + `_TEMPLATE.skill.md` |
| `profiles/` | AI expertise profiles (HR / finance / IT-security / general) |
| `registry/skills-index.json` | The signed source of truth: ids, versions, status, keywords, **allowed_services**, approval chains |
| `workflow/` | 8 importable n8n workflows (00–07) — agent, service gateway, approvals, SLA chaser, dashboard API, error handler, reset |
| `ui/index.html` | Chat-first portal (single file, no build): chat + preview cards, my-requests tracker, approvals inbox, governance/audit view; demo mode built in |
| `data/seeds/` | Synthetic registry seed (xlsx + CSVs, 6 tabs) — all fictional, labeled «تجريبي» |
| `docs/` | `submission.md` (AR+EN) · `setup-guide.md` · `demo-script.md` · `demo-extras/parking-permit.skill.md` (the live-add beat) |
| `tools/` | Generators: `build_workflows.py`, `build_data.py` (edit these, not the JSONs) |

## The six agent criteria

Runtime tool choice (model picks services; gateway enforces the allowlist) · plan-first reasoning (think tool) · memory (conversation + cross-run registry) · automatic triggers (webhook + 5-min schedule) · model-output branching (router, state machine, chaser decisions) · self-correction (deterministic working-day cross-check with forced re-reasoning, governance-denial recovery, retry+error workflow, needs_attention escalation).

## Quick start

`docs/setup-guide.md` (≈ 45 min, free tiers only). The portal runs instantly in demo mode by just opening `ui/index.html`.

> **Note:** this repo must stay **public** — n8n fetches `registry/` and `skills/` from raw.githubusercontent.com at runtime.

## Compliance

Individual work during the challenge period; AI coding assistants used (permitted & encouraged) — disclosed in `docs/submission.md`. 100% synthetic data. API keys only in n8n's credentials manager. No canned outputs — every decision is a live Gemini call, inspectable in n8n Executions.
