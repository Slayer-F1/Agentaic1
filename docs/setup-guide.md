# دليل الإعداد والتشغيل — Setup & Deployment Guide
## مُنجِز (Munjiz)

Follow in order. ≈ 40–50 minutes, free tiers only.

## 0. Prerequisites

- Docker Desktop (or Node 20+), a **demo** Google account (never a work account), and a free Google AI Studio key: <https://aistudio.google.com/apikey>.
- **This GitHub repo must be public** (it is: `Slayer-F1/Agentaic1`) — n8n fetches skills from `raw.githubusercontent.com` at runtime. If you fork it private, add a GitHub credential to the three "Fetch …" HTTP nodes instead.

## 1. Run n8n

```bash
docker run -d --name n8n -p 5678:5678 -e GENERIC_TIMEZONE=Asia/Dubai -e TZ=Asia/Dubai -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

Open <http://localhost:5678>, create the owner account.

## 2. The registry sheet

1. Create a Google Sheet named **Munjiz Registry** → File → Import → `data/seeds/munjiz-registry-seed.xlsx` → Replace spreadsheet. Six tabs: `Employees`, `LeaveBalances`, `ExpensePolicy`, `SystemCatalog`, `Transactions`, `AuditLog`.
2. Copy the spreadsheet ID from its URL.

## 3. Credentials (n8n → Credentials → Add)

1. **Google Gemini(PaLM) Api** — paste the AI Studio key (the only place it ever lives).
2. **Google Sheets OAuth2 API** + **Gmail OAuth2** — via a Google Cloud project (enable Sheets API + Gmail API, OAuth consent screen with your demo account as test user, Web-application client with n8n's callback URL). Same client works for both.

## 4. One find-and-replace, then import

In `workflow/*.json` replace `REPLACE_WITH_SPREADSHEET_ID` → your sheet ID (present in files 00, 02, 03, 04, 07 — a replace-across-all-files does it in one go).

Import order (Workflows → Import from File):

1. `00-data-io.json` → copy its workflow ID from the URL.
2. `02-service-gateway.json` → copy its ID.
3. Find-and-replace in the remaining files: `REPLACE_DATA_IO_ID` → (1), `REPLACE_GATEWAY_ID` → (2).
4. Import `01-chat-agent.json`, `03-approvals.json`, `04-sla-chaser.json`, `05-dashboard-api.json`, `06-error-handler.json`, `07-demo-reset.json`.
5. Open each workflow once and attach credentials on any ⚠ node.
6. Settings of 01/03/04/05 → Error workflow → `مُنجِز — 06 Error Handler`.
7. Activate: 01, 03, 04, 05, 07.

## 5. The portal

Open `ui/index.html` (or serve: `python -m http.server 8770`). It boots in demo mode. Settings → base URL `http://localhost:5678/webhook` → Save. The dot turns green.

## 6. Smoke test

1. As أحمد: «أريد إجازة الأسبوع القادم» → agent loads leave-request, asks for fields, warns about سالم's overlap, shows the preview → confirm → طلباتي shows it awaiting manager.
2. Switch persona to مريم → الاعتمادات → approve → أحمد's balance drops in the sidebar (LeaveBalances tab updated).
3. As أحمد: «أحتاج شهادة راتب للبنك» → preview → confirm → certificate with CERT number renders in طلباتي (auto-execute, no approval).
4. Governance proof: in a certificate chat ask «كم رصيد إجازتي؟» → the gateway denies get_leave_balance for that skill → red DENIED row in الحوكمة → audit.
5. الإعدادات → تشغيل حارس الإنجاز → the stale seeded claim (TXN-SEED-CHASE) triggers a remind/escalate email + audit rows.
6. **Live-add beat rehearsal:** copy `docs/demo-extras/parking-permit.skill.md` into `skills/`, append its JSON block to `registry/skills-index.json`, commit & push → within seconds «أريد تصريح موقف» works. No n8n change.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Portal stuck in demo mode | Base URL empty/wrong, or workflow 05 not Active. Use `/webhook`, not `/webhook-test`. |
| Skill not found / router says no match | Check `registry/skills-index.json` on GitHub raw (cache is ~1 min after a push) and that status = approved. |
| SERVICE_DENIED in normal flows | The skill's `allowed_services` doesn't list the service — that's governance working; fix the skill file if intentional. |
| Gemini 429 | Free-tier limit; nodes retry with backoff. Wait 60s. |
| Sheets "Could not find column" | Tab headers altered — re-import the seed xlsx. |
| Approve button says NOT_AUTHORIZED | You're not that employee's manager / your role ≠ stage. Switch persona. |
