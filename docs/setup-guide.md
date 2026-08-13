# دليل الإعداد والتشغيل — Setup & Deployment Guide
## مُنجِز (Munjiz)

Two paths: **Docker (recommended, ~5 min)** or manual. One credential total: a free Gemini key.

---

# A. Docker path

## A0. Prerequisites

- **Docker Desktop** running.
- A free Gemini API key: <https://aistudio.google.com/apikey>. That is the **only** credential the system needs — there is no Google Sheet, no OAuth client and no Gmail account. The datastore is n8n's own **Data Tables**.
- No external services and no network dependency at runtime: the skill library, profiles, memory and all records live in **n8n data tables**, seeded by `07 Provision & Seed` (`POST /munjiz/reset`). The repo is the authored source, not a runtime dependency.

## A1. Start the stack

```bash
cd docker && docker compose up -d
```

| Service | URL | What it is |
|---|---|---|
| `munjiz-n8n` | <http://localhost:5678> | n8n — workflows, data tables and the credential store (this machine uses **5679**; see `docker/.env`) |
| `munjiz-portal` | <http://localhost:8080> | the Munjiz portal (nginx), auto-pointed at n8n |

**Port already in use?** Copy `docker/.env.example` to `docker/.env` and change `N8N_PORT` / `PORTAL_PORT`. The portal picks the new port up automatically (it reads `/config.js`, which compose generates).

## A2. Create the n8n owner account — *only you can do this*

Open n8n and create the owner account (email + a password you choose). n8n does **not** register any webhook until the instance has an owner, so nothing works before this step.

## A3. Add the Gemini credential — *only you can do this*

n8n → **Credentials → Add** → search **"Google Gemini(PaLM) Api"** → paste your AI Studio key → Save. This is the only place any key ever lives (challenge security rule, and why this repo contains no secrets).

## A4. Deploy — one command

```bash
python tools/deploy.py
```

It binds your Gemini credential into every node that needs it, imports the workflows, activates them (sub-workflows included — n8n 2.x requires those active too), restarts n8n, **provisions the six data tables and loads the synthetic seed**, then verifies `GET /webhook/munjiz/state` returns real data.

Idempotent: workflows carry stable ids so re-running updates them in place, and the seed clears each table before loading it. Add `--split` for the 8-file granular set, or `--no-seed` to leave the data alone.

The one thing it cannot set is **Settings → Error workflow → `مُنجِز — 06 Error Handler`** on `01-main` — do that once in the UI.

## A6. Use it

Open <http://localhost:8080>. The connection dot turns green ("متصل") on its own — no configuration needed.

## A7. Everyday commands

```bash
docker compose logs -f n8n
```

```bash
docker compose restart n8n
```

```bash
docker compose down
```

The n8n data (workflows + encrypted credentials) lives in the `munjiz_n8n_data` volume and survives `down`. To wipe everything: `docker compose down && docker volume rm munjiz_n8n_data`.

---

# B. Manual path (no Docker)

1. `npx n8n` (Node 20+), then open <http://localhost:5678> and create the owner account.
2. Add the Gemini credential (step **A3** above).
3. There are **no placeholders to replace** — sub-workflow links resolve via stable workflow ids, and the datastore is internal to n8n.
4. n8n → **Workflows → Import from File** → import the 4 files in `workflow/` in any order (or the 8 in `workflow-split/` — one set or the other, never both).
5. Attach credentials, set **Settings → Error workflow** on `01-main`, and activate **all four** (the two sub-workflows included — on n8n 2.x a called sub-workflow must be active or the caller fails).
6. Open `ui/index.html`, then **الإعدادات / Settings** → base URL `http://localhost:5678/webhook` → Save.

---

# Smoke test

1. As أحمد: «أريد إجازة الأسبوع القادم» → the agent loads `leave-request`, asks for the missing fields, warns about سالم's overlapping approved leave, and shows a preview card → confirm → **طلباتي** shows it awaiting the manager.
2. Switch the persona to مريم → **الاعتمادات** → approve → أحمد's balance drops (the `LeaveBalances` data table updates).
3. As أحمد: «أحتاج شهادة راتب للبنك» → preview → confirm → the certificate renders with a CERT number (auto-execute, no approval chain).
4. **Governance proof:** inside a certificate conversation ask «كم رصيد إجازتي؟» → the gateway refuses `get_leave_balance` for that skill → a red DENIED row appears under **الحوكمة**.
5. **الإعدادات → تشغيل حارس الإنجاز** → the seeded 30-hour-old claim is picked up and the model's remind/escalate decision lands in the audit log.
6. **Learning loop:** fire `POST /munjiz/reflect` (or wait for its schedule) → a memory fact appears in the Governance learning strip and a skill-improvement proposal lands **pending** → approve it there → the skill's **version bumps** and the rule is written into its body.
7. **Certificate PDF:** in طلباتي open the executed certificate → **تنزيل الشهادة (PDF)** → sealed, watermarked A4 opens print-ready.
8. **Dynamic chips:** every collection question arrives with tap-to-answer options («سنوية/مرضية/طارئة», common addressees, computed date ranges).
9. **Live-add:** adding a procedure = one row in the `Skills` table (or a skill .md + rebuild + `deploy.py`) — no workflow changes.

# Troubleshooting

| Symptom | Fix |
|---|---|
| Webhooks 404 / portal stays amber | Owner account not created (step A2), or the workflow isn't active. Both are required before n8n registers a webhook. |
| `Workflow is not active and cannot be executed` | **n8n 2.x only:** a called sub-workflow must itself be active. `tools/deploy.py` activates every workflow it deploys (including `00 Data IO` and `02 Service Gateway`); if you imported by hand, activate those two as well. |
| Webhook returns HTTP 200 with an empty body | The workflow ran but stopped before its Respond node — nearly always a missing credential. Open **n8n → Executions** and look at the red node. |
| `port is already allocated` on compose up | Another container owns 5678/8080 — set `N8N_PORT` / `PORTAL_PORT` in `docker/.env`. |
| Portal stuck in demo mode | It couldn't reach n8n. Check `docker compose ps`, and that Settings' base URL ends in `/webhook` (not `/webhook-test`). |
| Skill not found / router says no match | Check the raw registry URL loads and the skill's `status` is `approved`. GitHub's raw cache lags ~1 minute after a push. |
| `SERVICE_DENIED_BY_GOVERNANCE` | The skill's `allowed_services` doesn't include that service — governance working as designed. Edit the skill file if it was intentional. |
| Gemini 429 | Free-tier rate limit; the nodes retry with backoff. Wait 60s. |
| A table looks empty or stale | Re-run the seed: the portal's **إعادة تهيئة العرض** button, or `POST /webhook/munjiz/reset`. |
| Approve/Reject toasts NOT_AUTHORIZED or NOT_PENDING | You're not that employee's manager / your role ≠ the current stage, or someone already decided. |
| `import:workflow` says "Importing 0 workflows" in Git Bash | MSYS rewrote the container path. Use `tools/deploy.py` (it avoids the shell), or prefix with `MSYS_NO_PATHCONV=1`. |
