# دليل الإعداد والتشغيل — Setup & Deployment Guide
## مُنجِز (Munjiz)

Two paths: **Docker (recommended, ~15 min)** or manual. Free tiers only, no paid services.

---

# A. Docker path

## A0. Prerequisites

- **Docker Desktop** running.
- A **demo** Google account (never your work account) — it owns the Sheet, the Gmail inbox, and the AI Studio key.
- A free Gemini API key: <https://aistudio.google.com/apikey>.
- **This repo must stay public** — n8n fetches `registry/skills-index.json` and `skills/*.md` from raw.githubusercontent.com at runtime. If you fork it private, add a GitHub credential to the five "Fetch …" HTTP nodes (three in workflow 01, one each in 02 and 05).

## A1. Start the stack

```bash
cd docker && docker compose up -d
```

That brings up two containers:

| Service | URL | What it is |
|---|---|---|
| `munjiz-n8n` | <http://localhost:5678> | n8n — workflows and the credential store |
| `munjiz-portal` | <http://localhost:8080> | the Munjiz portal (nginx), auto-pointed at n8n |

**Port already in use?** Copy `docker/.env.example` to `docker/.env` and change `N8N_PORT` / `PORTAL_PORT`. The portal picks the new port up automatically (it reads `/config.js`, which compose generates).

## A2. Create the n8n owner account — *only you can do this*

Open n8n and create the owner account (email + a password you choose). n8n does **not** register any webhook until the instance has an owner, so nothing works before this step.

## A3. The registry sheet

1. In the demo Google account, create a Sheet named **Munjiz Registry**.
2. **File → Import → Upload** `data/seeds/munjiz-registry-seed.xlsx` → **Replace spreadsheet**. You get six tabs: `Employees`, `LeaveBalances`, `ExpensePolicy`, `SystemCatalog`, `Transactions`, `AuditLog`.
3. Copy the spreadsheet ID from the URL: `docs.google.com/spreadsheets/d/<THIS>/edit`.

## A4. Credentials — *only you can do this*

In n8n → **Credentials → Add**. These are the only place any key ever lives (challenge security rule, and the reason the repo contains no secrets):

1. **Google Gemini(PaLM) Api** → paste your AI Studio key.
2. **Google Sheets OAuth2 API** and **Gmail OAuth2** → via a Google Cloud project: enable the Sheets API and Gmail API, configure the OAuth consent screen (External, your demo account as a test user), create a **Web application** OAuth client, and paste the client ID/secret. Use the callback URL n8n shows you (`http://localhost:5678/rest/oauth2-credential/callback`), then click **Connect** and sign in with the demo account.

## A5. Deploy the workflows

```bash
python tools/deploy.py --spreadsheet-id YOUR_SHEET_ID
```

The script stages the workflows with your sheet ID, binds the credentials you created, imports them, activates all of them (sub-workflows included — n8n 2.x needs those active too), restarts n8n, and verifies `GET /webhook/munjiz/state`. Add `--split` to deploy the 8-file granular set instead of the merged 4-file one; it deactivates the other set first so the shared webhook paths never compete. It is **idempotent** — the workflows carry stable ids, so re-running updates them in place instead of creating duplicates.

Then open each workflow once in the n8n UI and pick your credentials on any node showing a ⚠ (n8n remembers per credential type, so it's quick), and set **Settings → Error workflow → `مُنجِز — 06 Error Handler`** on workflows 01, 03, 04, 05. Re-run the deploy script afterwards if you prefer, or just save in the UI.

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
2. Do steps **A3** and **A4** above.
3. In `workflow/*.json`, replace `REPLACE_WITH_SPREADSHEET_ID` with your sheet ID — it is the **only** placeholder left (sub-workflow links resolve on their own via stable workflow ids). It appears in files 00, 02, 03, 04, 07.
4. n8n → **Workflows → Import from File** → import the 4 files in `workflow/` in any order (or the 8 in `workflow-split/` — one set or the other, never both).
5. Attach credentials, set **Settings → Error workflow** on `01-main`, and activate **all four** (the two sub-workflows included — on n8n 2.x a called sub-workflow must be active or the caller fails).
6. Open `ui/index.html`, then **الإعدادات / Settings** → base URL `http://localhost:5678/webhook` → Save.

---

# Smoke test

1. As أحمد: «أريد إجازة الأسبوع القادم» → the agent loads `leave-request`, asks for the missing fields, warns about سالم's overlapping approved leave, and shows a preview card → confirm → **طلباتي** shows it awaiting the manager.
2. Switch the persona to مريم → **الاعتمادات** → approve → أحمد's balance drops (the `LeaveBalances` tab updates).
3. As أحمد: «أحتاج شهادة راتب للبنك» → preview → confirm → the certificate renders with a CERT number (auto-execute, no approval chain).
4. **Governance proof:** inside a certificate conversation ask «كم رصيد إجازتي؟» → the gateway refuses `get_leave_balance` for that skill → a red DENIED row appears under **الحوكمة**.
5. **الإعدادات → تشغيل حارس الإنجاز** → the seeded 30-hour-old claim triggers a remind/escalate email plus audit rows.
6. **Live-add rehearsal:** copy `docs/demo-extras/parking-permit.skill.md` into `skills/`, append its JSON block to `registry/skills-index.json`, commit and push → within a minute «أريد تصريح موقف» works, with no n8n change at all.

# Troubleshooting

| Symptom | Fix |
|---|---|
| Webhooks 404 / portal stays amber | Owner account not created (step A2), or the workflow isn't active. Both are required before n8n registers a webhook. |
| `Workflow is not active and cannot be executed` | **n8n 2.x only:** a called sub-workflow must itself be active. `tools/deploy.py` activates all 8 (including `00 Data IO` and `02 Service Gateway`); if you imported by hand, activate those two as well. |
| Webhook returns HTTP 200 with an empty body | The workflow ran but stopped before its Respond node — nearly always a missing credential. Open **n8n → Executions** and look at the red node. |
| `port is already allocated` on compose up | Another container owns 5678/8080 — set `N8N_PORT` / `PORTAL_PORT` in `docker/.env`. |
| Portal stuck in demo mode | It couldn't reach n8n. Check `docker compose ps`, and that Settings' base URL ends in `/webhook` (not `/webhook-test`). |
| Skill not found / router says no match | Check the raw registry URL loads and the skill's `status` is `approved`. GitHub's raw cache lags ~1 minute after a push. |
| `SERVICE_DENIED_BY_GOVERNANCE` | The skill's `allowed_services` doesn't include that service — governance working as designed. Edit the skill file if it was intentional. |
| Gemini 429 | Free-tier rate limit; the nodes retry with backoff. Wait 60s. |
| Sheets "Could not find column" | Tab headers were altered — re-import the seed workbook. |
| Approve/Reject toasts NOT_AUTHORIZED or NOT_PENDING | You're not that employee's manager / your role ≠ the current stage, or someone already decided. |
| `import:workflow` says "Importing 0 workflows" in Git Bash | MSYS rewrote the container path. Use `tools/deploy.py` (it avoids the shell), or prefix with `MSYS_NO_PATHCONV=1`. |
