# مُنجِز — Munjiz

Entry for the **AI Agents Innovation Challenge** (تحدي ابتكار وكلاء الذكاء الاصطناعي): **one** generic AI agent that completes all routine employee/government transactions conversationally — governed by **skills-as-code**.

Every procedure is a versioned, approved `SKILL.md` in this repo (fields, eligibility rules, allowed services, approval chain, escalation) + a `PROFILE.md` persona. The n8n agent loads the matching skill **live from GitHub** per request, becomes that procedure's expert, and every data/tool call passes a **service gateway** that enforces the skill's allowlist and writes an audit row — including denials. Adding a new procedure = pushing one markdown file. Zero n8n changes.

Built on **n8n + Google Gemini 2.5 Flash (free tier)**, with **n8n Data Tables** as the transactional datastore — no spreadsheet, no OAuth, no external service — and a bilingual RTL chat-first portal.

## Repository map

| Path | Contents |
|---|---|
| `skills/` | The governed skill library (leave, salary certificate, expense claim, IT access) + `_TEMPLATE.skill.md` |
| `profiles/` | AI expertise profiles (HR / finance / IT-security / general) |
| `registry/skills-index.json` | The signed source of truth: ids, versions, status, keywords, **allowed_services**, approval chains |
| `docker/` | One-command local stack: n8n + the portal (`cd docker && docker compose up -d`) |
| `workflow/` | **4 importable n8n workflows** — `01-main` (chat + approvals + SLA chaser + dashboard API + reset on one canvas), plus `00-data-io`, `02-service-gateway` and `03-error-handler`, which must stay separate: the first two are invoked via `executeWorkflow`/`toolWorkflow` (which can only target another workflow) and the third is assigned as the error workflow. Stable ids, so links resolve on import |
| `workflow-split/` | The same system as 8 single-purpose workflows — easier to walk through node by node during the judges’ inspection. Import **one** set or the other, never both (identical webhook paths). `python tools/deploy.py --split` |
| `ui/index.html` | Chat-first portal (single file, no build): chat + preview cards, my-requests tracker, approvals inbox, governance/audit view; demo mode built in |
| `data/seeds/` | Synthetic registry seed (xlsx + CSVs, 6 tabs) — all fictional, labeled «تجريبي» |
| `docs/` | `submission.md` (AR+EN) · `setup-guide.md` · `demo-script.md` · `demo-extras/parking-permit.skill.md` (the live-add beat) |
| `tools/` | `build_workflows.py`, `build_data.py` (edit these, not the JSONs) · `deploy.py` — imports, publishes and verifies the stack in one command |

## The six agent criteria

Runtime tool choice (model picks services; gateway enforces the allowlist) · plan-first reasoning (think tool) · memory (conversation + cross-run registry) · automatic triggers (webhook + 5-min schedule) · model-output branching (router, state machine, chaser decisions) · self-correction (deterministic working-day cross-check with forced re-reasoning, governance-denial recovery, retry+error workflow, needs_attention escalation).

## Quick start

```bash
cd docker && docker compose up -d
```

n8n comes up on <http://localhost:5678> and the portal on <http://localhost:8080>. Then follow `docs/setup-guide.md` (≈ 5 min): create the n8n owner account, add **one** credential (your Gemini key), and run:

```bash
python tools/deploy.py
```

To just look at the interface, open `ui/index.html` directly — it runs in demo mode with no setup at all.

> **Note:** the runtime skill library lives **inside n8n** (the `Skills` and `Profiles` data
> tables, seeded from `skills/` and `profiles/`). The repo is the authored source and the
> submission artifact; nothing is fetched over the network at runtime, and an approved
> proposal rewrites the stored skill and bumps its version — so procedures actually improve.

## Compliance

Individual work during the challenge period; AI coding assistants used (permitted & encouraged) — disclosed in `docs/submission.md`. 100% synthetic data. API keys only in n8n's credentials manager. No canned outputs — every decision is a live Gemini call, inspectable in n8n Executions.
