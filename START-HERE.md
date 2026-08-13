# مُنجِز — تشغيل على جهاز جديد | Munjiz — Fresh PC Start

Everything you need is in this folder. **5 steps, ~10 minutes, one credential.**

## What you need installed

1. **Docker Desktop** (running)
2. **Python 3** (any recent version — used only by the deploy script)
3. A free **Gemini API key**: <https://aistudio.google.com/apikey>
   *(Recommended for demo day: enable billing on the AI Studio project — it stays free at this volume but lifts the very small new-project daily quota.)*

## The 5 steps

```bash
cd docker
docker compose up -d
```

1. ⬆ starts **n8n** (http://localhost:5678) and the **portal** (http://localhost:8080). If a port is taken, copy `docker/.env.example` to `docker/.env` and change it — everything adapts.
2. Open **http://localhost:5678** → create the n8n **owner account** (any email + password — it's local).
3. n8n → **Credentials → Add** → search **"Google Gemini(PaLM) Api"** → paste your key → Save.
4. From this folder:
   ```bash
   python tools/deploy.py
   ```
   It imports the workflows, activates them, binds your credential into every node, provisions the data tables, loads the synthetic demo data, and verifies the API responds.
5. Open **http://localhost:8080** — the dot turns green (**متصل**) by itself. Done.

One optional click in n8n: open `مُنجِز — Main` → Settings → **Error workflow** → `مُنجِز — 06 Error Handler`.

## Where things are

| | |
|---|---|
| `workflow/` | The 4 n8n workflow files (imported for you by the script) |
| `workflow-split/` | Same system as 8 granular workflows, for node-by-node inspection |
| `ui/index.html` | The portal (also runs standalone in demo mode — just double-click it) |
| `docs/setup-guide.md` | Full guide + smoke test + troubleshooting |
| `docs/demo-script.md` | The 8-minute live demo, beat by beat |
| `docs/submission.md` | The official challenge submission document (AR + EN) |

**Reset demo data anytime:** the portal's الإعدادات → إعادة تهيئة العرض button.
