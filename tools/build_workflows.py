# -*- coding: utf-8 -*-
"""Builds the importable n8n workflow JSONs for Munjiz (مُنجِز) — skill-governed transactions agent.

Run:  python tools/build_workflows.py     → workflow/*.json

User-replaced placeholders (find & replace before import):
The GitHub raw base defaults to the real Agentaic1 repo (public) and can be edited in one node.
"""
import json
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "workflow")
OUT_SPLIT = os.path.join(ROOT, "workflow-split")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
# Background cadence. The Gemini free tier on a newly created project is very small
# (metric generate_content_free_tier_requests, limit 20), and each scheduled agent
# tick spends model calls even when nothing needs doing - which would drain the
# day's allowance before a demo starts. The schedule nodes stay in the workflow to
# satisfy criterion 4 (automatic, not manual), but idle at a low frequency; the demo
# fires them on demand through the UI button and the /munjiz/reflect webhook.
CHASER_HOURS = 12
REFLECT_HOURS = 24
MODEL_MAIN = "gemini-2.5-flash"        # employee-facing reasoning
# NOTE: gemini-2.5-flash-lite would have a larger free allowance, but it 404s for
# newly created API projects ("no longer available to new users"), so every call
# runs on flash. Quota is therefore managed by cadence, not by model tier.
MODEL_CHEAP = MODEL_MAIN
GEMINI_URL = GEMINI_BASE + MODEL_MAIN + ":generateContent"
RAW_BASE = "https://raw.githubusercontent.com/Slayer-F1/Agentaic1/main/"
DEMO_INBOX = "munjiz.demo.uae@gmail.com"

CRED_GEMINI = {"googlePalmApi": {"id": "GEMINI_CRED_ID", "name": "Google Gemini (AI Studio)"}}


import build_data  # single source of seed truth (tools/ is on sys.path when run as a script)


def js_lit(obj):
    """A JS string literal holding this object as JSON - no manual escaping anywhere."""
    return json.dumps(json.dumps(obj, ensure_ascii=False))


def seed_rows(table):
    headers, rows = build_data.TABS[table]
    return [{k: ("" if r.get(k) is None else r.get(k)) for k in headers} for r in rows]


def nid():
    return str(uuid.uuid4())


def node(name, ntype, tv, pos, params, credentials=None, webhook=False, **extra):
    n = {"id": nid(), "name": name, "type": ntype, "typeVersion": tv,
         "position": list(pos), "parameters": params}
    if credentials:
        n["credentials"] = credentials
    if webhook:
        n["webhookId"] = nid()
    n.update(extra)
    return n


def sticky(content, pos, width=520, height=220, color=4):
    return node("Note " + nid()[:8], "n8n-nodes-base.stickyNote", 1, pos,
                {"content": content, "width": width, "height": height, "color": color})


# Stable workflow ids (16-char, n8n keeps them verbatim on import). Because the
# ids are deterministic, sub-workflow references resolve with no manual wiring and
# re-importing UPDATES a workflow in place instead of creating duplicates.
WF_IDS = {
    "00-data-io.json": "munjizDataIo0000",
    "01-chat-agent.json": "munjizChatAgent1",
    "02-service-gateway.json": "munjizGateway002",
    "03-approvals.json": "munjizApprovals3",
    "04-sla-chaser.json": "munjizSlaChaser4",
    "05-dashboard-api.json": "munjizDashApi005",
    "06-error-handler.json": "munjizErrorHnd06",
    "07-demo-reset.json": "munjizDemoReset7",
}
WF_IDS["08-reflection.json"] = "munjizReflect008"
WF_IDS["09-patch-review.json"] = "munjizPatchRev09"
WF_IDS["01-main.json"] = "munjizMain000001"
WF_IDS["03-error-handler.json"] = WF_IDS["06-error-handler.json"]
WF_MAIN_ID = WF_IDS["01-main.json"]
MAIN_NAME = "مُنجِز — Main (chat + approvals + SLA + API + reset)"
DATA_IO_ID = WF_IDS["00-data-io.json"]
GATEWAY_ID = WF_IDS["02-service-gateway.json"]


class Wf:
    def __init__(self, name, wf_id=None):
        self.name, self.nodes, self.conns = name, [], {}
        self.wf_id = wf_id

    def add(self, n):
        self.nodes.append(n)
        return n["name"]

    def link(self, src, dst, ctype="main", output=0, dst_index=0):
        e = self.conns.setdefault(src, {}).setdefault(ctype, [])
        while len(e) <= output:
            e.append([])
        e[output].append({"node": dst, "type": ctype, "index": dst_index})

    def dump(self):
        doc = {"name": self.name, "nodes": self.nodes, "connections": self.conns,
               "settings": {"executionOrder": "v1"}, "pinData": {}}
        if self.wf_id:
            doc["id"] = self.wf_id
        return doc


DT_TYPE = "n8n-nodes-base.dataTable"
DT_VER = 1.1


def dt_ref(table):
    """Data tables are addressable by name, so no generated ids leak into the JSON."""
    return {"__rl": True, "mode": "name", "value": table}


def dt_map():
    return {"mappingMode": "autoMapInputData", "value": None, "matchingColumns": [],
            "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True}


def dt_read(name, table, pos, dyn=None, newest=None):
    """Read a table. `newest=N` returns only the N most recent rows, which stops an
    append-only log (AuditLog) from slowing every dashboard poll as it grows."""
    params = {
        "operation": "get",
        "dataTableId": dt_ref(dyn or table),
        "matchType": "allConditions",
        "filters": {"conditions": []},
        "options": {},
    }
    if newest:
        params.update({"returnAll": False, "limit": newest, "orderBy": True,
                       "orderByColumn": "createdAt", "orderByDirection": "DESC"})
    else:
        params["returnAll"] = True
    # executeOnce is essential: a Data Table read runs once PER INPUT ITEM, and these
    # reads ignore their input. Chained without it, each read multiplies the previous
    # one's row count (7 employees -> 49 balances -> 147 transactions).
    return node(name, DT_TYPE, DT_VER, pos, params, executeOnce=True,
                alwaysOutputData=True, retryOnFail=True, maxTries=3, waitBetweenTries=2000)


def dt_insert(name, table, pos):
    return node(name, DT_TYPE, DT_VER, pos, {
        "operation": "insert",
        "dataTableId": dt_ref(table),
        "columns": dt_map(),
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=2000)


def dt_upsert(name, table, match, pos):
    return node(name, DT_TYPE, DT_VER, pos, {
        "operation": "upsert",
        "dataTableId": dt_ref(table),
        "matchType": "allConditions",
        "filters": {"conditions": [
            {"keyName": match, "condition": "eq", "keyValue": "={{ $json." + match + " }}"}]},
        "columns": dt_map(),
        "options": {},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=2000)


def code(name, js, pos, **extra):
    return node(name, "n8n-nodes-base.code", 2, pos, {"jsCode": js}, **extra)


def gemini(name, pos, field="geminiBody", model="gemini-2.5-flash"):
    """model is overridable, but note gemini-2.5-flash-lite is NOT available to
    newly created API projects (404 "no longer available to new users")."""
    return node(name, "n8n-nodes-base.httpRequest", 4.2, pos,
                {"method": "POST",
                 "url": GEMINI_BASE + model + ":generateContent",
                 "authentication": "predefinedCredentialType", "nodeCredentialType": "googlePalmApi",
                 "sendBody": True, "specifyBody": "json",
                 "jsonBody": "={{ JSON.stringify($json." + field + ") }}",
                 "options": {"timeout": 90000}},
                credentials=CRED_GEMINI, retryOnFail=True, maxTries=2, waitBetweenTries=15000)


def http_raw(name, url_expr, pos):
    return node(name, "n8n-nodes-base.httpRequest", 4.2, pos,
                {"method": "GET", "url": url_expr, "options": {"timeout": 20000,
                 "response": {"response": {"responseFormat": "text"}}}},
                retryOnFail=True, maxTries=3, waitBetweenTries=3000)


def respond(name, body_expr, pos):
    return node(name, "n8n-nodes-base.respondToWebhook", 1.2, pos,
                {"respondWith": "json", "responseBody": body_expr,
                 "options": {"responseHeaders": {"entries": [
                     {"name": "Access-Control-Allow-Origin", "value": "*"},
                     {"name": "Access-Control-Allow-Headers", "value": "Content-Type"}]}}})


def rm_schema(fields):
    """ResourceMapper field descriptors for a sub-workflow's declared inputs.

    Required: n8n only evaluates the mapped values when this array is non-empty
    (see WorkflowToolService.useSchema), otherwise the tool degrades to passing a
    single opaque `query` string.
    """
    return [{"id": f, "displayName": f, "required": False, "defaultMatch": False,
             "display": True, "canBeUsedToMatch": True, "type": "string"} for f in fields]


def wfref(placeholder, cached):
    return {"__rl": True, "value": placeholder, "mode": "list", "cachedResultName": cached}


def exec_wf(name, placeholder, cached, values, pos):
    return node(name, "n8n-nodes-base.executeWorkflow", 1.2, pos,
                {"source": "database", "workflowId": wfref(placeholder, cached),
                 "workflowInputs": {"mappingMode": "defineBelow", "value": values,
                                    "matchingColumns": [], "schema": [],
                                    "attemptToConvertTypes": False, "convertFieldsToString": False},
                 "options": {"waitForSubWorkflow": True}})


def if_node(name, left, op_type, op, right, pos, single=False):
    cond = {"leftValue": left, "rightValue": right, "operator": {"type": op_type, "operation": op}}
    if single:
        cond["operator"]["singleValue"] = True
    return node(name, "n8n-nodes-base.if", 2.2, pos,
                {"conditions": {"options": {"caseSensitive": True, "leftValue": "",
                                            "typeValidation": "loose", "version": 2},
                                "conditions": [cond], "combinator": "and"},
                 "options": {}})


def switch_rules(name, left_expr, keys, pos):
    vals = []
    for k in keys:
        vals.append({"conditions": {"options": {"caseSensitive": True, "leftValue": "",
                                                "typeValidation": "loose", "version": 2},
                                    "conditions": [{"leftValue": left_expr, "rightValue": k,
                                                    "operator": {"type": "string", "operation": "equals"}}],
                                    "combinator": "and"},
                     "renameOutput": True, "outputKey": k})
    return node(name, "n8n-nodes-base.switch", 3.2, pos, {"rules": {"values": vals}, "options": {}})


GPARSE = (
    "const out = [];\n"
    "for (const item of $input.all()) {\n"
    "  let text = '';\n"
    "  try { text = item.json.candidates[0].content.parts.map(p => p.text || '').join(''); } catch (e) {}\n"
    "  const cleaned = text.replace(/^```(json)?/m, '').replace(/```\\s*$/m, '').trim();\n"
    "  let parsed = null;\n"
    "  try { parsed = JSON.parse(cleaned); } catch (e) {\n"
    "    const m = cleaned.match(/\\{[\\s\\S]*\\}/);\n"
    "    if (m) { try { parsed = JSON.parse(m[0]); } catch (e2) {} }\n"
    "  }\n"
    "  out.push({ json: { gemini_text: cleaned, gemini_json: parsed, gemini_ok: !!parsed } });\n"
    "}\n"
    "return out;\n"
)

WORKDAY_JS = (
    "function workingDays(startISO, endISO) {\n"
    "  const s = new Date(startISO + 'T12:00:00Z'), e = new Date(endISO + 'T12:00:00Z');\n"
    "  if (isNaN(s) || isNaN(e) || e < s) return null;\n"
    "  let n = 0; const d = new Date(s);\n"
    "  while (d <= e) { const w = d.getUTCDay(); if (w !== 6 && w !== 0) n++; d.setUTCDate(d.getUTCDate() + 1); }\n"
    "  return n;\n"
    "}\n"
)


# ---------------------------------------------------------------------------
# 00 — Data IO (sub)
# ---------------------------------------------------------------------------

def build_data_io():
    wf = Wf("مُنجِز — 00 Data IO (sub)")
    trig = wf.add(node("Data Input", "n8n-nodes-base.executeWorkflowTrigger", 1.1, (-700, 0),
                       {"inputSource": "workflowInputs",
                        "workflowInputs": {"values": [{"name": "action", "type": "string"},
                                                      {"name": "tab", "type": "string"}]}}))
    sw = wf.add(switch_rules("Action?", "={{ $json.action }}", ["read", "read_all"], (-460, 0)))
    wf.link(trig, sw)

    rt = wf.add(dt_read("Read Tab", "Employees", (-200, -140),
                            dyn="={{ $('Data Input').first().json.tab }}"))
    wrap = wf.add(code("Wrap Rows", (
        "const rows = $input.all().map(i => i.json).filter(r => r && Object.keys(r).length > 0);\n"
        "return [{ json: { tab: $('Data Input').first().json.tab, count: rows.length, rows } }];\n"
    ), (60, -140)))
    wf.link(sw, rt, output=0)
    wf.link(rt, wrap)

    # Only what read_all's consumers need: the dashboard uses employees/balances/
    # transactions/audit and the SLA chaser uses transactions/employees. ExpensePolicy
    # and SystemCatalog are read directly by the gateway, so they stay out of here.
    tabs = ["Employees", "LeaveBalances", "Transactions", "AuditLog", "Memory",
            "SkillPatches", "Skills"]
    prev = None
    x = -200
    for t in tabs:
        n = wf.add(dt_read("Read " + t, t, (x, 140), newest=120 if t == "AuditLog" else None))
        if prev is None:
            wf.link(sw, n, output=1)
        else:
            wf.link(prev, n)
        prev = n
        x += 220
    asm = wf.add(code("Assemble All", (
        "const grab = (n) => { try { return $(n).all().map(i => i.json).filter(r => r && Object.keys(r).length > 0); } catch (e) { return []; } };\n"
        "return [{ json: {\n"
        "  employees: grab('Read Employees'), balances: grab('Read LeaveBalances'),\n"
        "  transactions: grab('Read Transactions'), audit: grab('Read AuditLog'),\n"
        "  memory: grab('Read Memory'), patches: grab('Read SkillPatches'),\n"
        "  skills: grab('Read Skills'),\n"
        "} }];\n"
    ), (x, 140)))
    wf.link(prev, asm)
    wf.nodes.append(sticky("## Data IO (sub)\nUnified reads over the Munjiz Registry sheet. "
                           "Tabs: Employees · LeaveBalances · ExpensePolicy · SystemCatalog · "
                           "Transactions · AuditLog.", (-720, -320)))
    return wf


# ---------------------------------------------------------------------------
# 02 — Service Gateway (sub): allowlist enforcement + audit on EVERY call
# ---------------------------------------------------------------------------

GATE_CHECK_JS = (
    "const inp = $('Gateway Input').first().json;\n"
    "// allowlist comes from the live Skills table, so an approved change takes effect at once\n"
    "const rows = $input.all().map(i => i.json).filter(r => r && r.skill_id);\n"
    "const row = rows.find(r => r.skill_id === inp.skill_id && r.status === 'approved');\n"
    "const skill = row ? { id: row.skill_id, title_ar: row.title_ar,\n"
    "  allowed_services: String(row.allowed_services || '').split(';').filter(Boolean),\n"
    "  approval_chain: String(row.approval_chain || '').split(';').filter(Boolean),\n"
    "  auto_execute: String(row.auto_execute) === 'true',\n"
    "  sla_hours: Number(row.sla_hours) || 48 } : null;\n"
    "let payload = {};\n"
    "try { payload = inp.payload ? JSON.parse(inp.payload) : {}; } catch (e) { payload = { _raw: inp.payload }; }\n"
    "const allowed = skill ? (skill.allowed_services || []) : [];\n"
    "const denied = !skill || !allowed.includes(inp.service);\n"
    "return [{ json: {\n"
    "  service: inp.service, skill_id: inp.skill_id, employee_id: inp.employee_id,\n"
    "  session_id: inp.session_id || '', payload,\n"
    "  denied, allowed_services: allowed,\n"
    "  skill_meta: skill ? { approval_chain: skill.approval_chain, auto_execute: skill.auto_execute,\n"
    "    sla_hours: skill.sla_hours, title_ar: skill.title_ar } : null,\n"
    "} }];\n"
)

SVC_CODES = {
    "get_employee_profile": (
        "const j = $('Gate Check').first().json;\n"
        "const rows = $input.all().map(i => i.json);\n"
        "const e = rows.find(r => r.employee_id === j.employee_id);\n"
        "if (!e) return [{ json: { ...j, result: { error: 'EMPLOYEE_NOT_FOUND' } } }];\n"
        "return [{ json: { ...j, result: {\n"
        "  employee_id: e.employee_id, name_ar: e.name_ar, name_en: e.name_en, role: e.role,\n"
        "  department: e.department, grade: e.grade, manager_id: e.manager_id, status: e.status,\n"
        "  joined_date: e.joined_date,\n"
        "} } }];\n"
    ),
    "get_leave_balance": (
        "const j = $('Gate Check').first().json;\n"
        "const rows = $input.all().map(i => i.json);\n"
        "const b = rows.find(r => r.employee_id === j.employee_id);\n"
        "if (!b) return [{ json: { ...j, result: { error: 'BALANCE_NOT_FOUND' } } }];\n"
        "return [{ json: { ...j, result: {\n"
        "  annual_total: +b.annual_total, annual_used: +b.annual_used,\n"
        "  annual_remaining: +b.annual_total - +b.annual_used,\n"
        "  sick_total: +b.sick_total, sick_used: +b.sick_used,\n"
        "  sick_remaining: +b.sick_total - +b.sick_used,\n"
        "} } }];\n"
    ),
    "get_salary_record": (
        "const j = $('Gate Check').first().json;\n"
        "const emps = $('Read Employees (salary)').all().map(i => i.json);\n"
        "const txns = $input.all().map(i => i.json);\n"
        "const e = emps.find(r => r.employee_id === j.employee_id);\n"
        "if (!e) return [{ json: { ...j, result: { error: 'EMPLOYEE_NOT_FOUND' } } }];\n"
        "const month = new Date().toISOString().slice(0, 7);\n"
        "const certs = txns.filter(t => t.employee_id === j.employee_id && t.skill_id === 'salary-certificate'\n"
        "  && String(t.ts || '').startsWith(month) && t.status === 'executed').length;\n"
        "return [{ json: { ...j, result: {\n"
        "  name_ar: e.name_ar, name_en: e.name_en, role: e.role, grade: e.grade,\n"
        "  joined_date: e.joined_date, status: e.status,\n"
        "  monthly_salary_aed: +e.monthly_salary_aed, allowances_aed: +e.allowances_aed,\n"
        "  certificates_issued_this_month: certs, monthly_limit: 3,\n"
        "} } }];\n"
    ),
    "get_expense_policy": (
        "const j = $('Gate Check').first().json;\n"
        "const pol = $input.all().map(i => i.json);\n"
        "const txns = $('Read Transactions (policy)').all().map(i => i.json);\n"
        "const cat = j.payload.category || '';\n"
        "const p = pol.find(r => r.category === cat);\n"
        "if (!p) return [{ json: { ...j, result: { error: 'UNKNOWN_CATEGORY', categories: pol.map(r => r.category) } } }];\n"
        "const month = new Date().toISOString().slice(0, 7);\n"
        "let spent = 0;\n"
        "for (const t of txns) {\n"
        "  if (t.employee_id !== j.employee_id || t.skill_id !== 'expense-claim') continue;\n"
        "  if (!String(t.ts || '').startsWith(month)) continue;\n"
        "  if (!['executed', 'awaiting_manager', 'awaiting_finance'].includes(t.status)) continue;\n"
        "  try { const pl = JSON.parse(t.payload_json || '{}'); if (pl.category === cat) spent += +pl.amount_aed || 0; } catch (e) {}\n"
        "}\n"
        "return [{ json: { ...j, result: {\n"
        "  category: cat, monthly_cap_aed: +p.monthly_cap_aed,\n"
        "  receipt_required_above: +p.receipt_required_above,\n"
        "  spent_this_month_aed: Math.round(spent * 100) / 100,\n"
        "  remaining_this_month_aed: Math.round((+p.monthly_cap_aed - spent) * 100) / 100,\n"
        "  notes: p.notes || '',\n"
        "} } }];\n"
    ),
    "get_it_roles": (
        "const j = $('Gate Check').first().json;\n"
        "const rows = $input.all().map(i => i.json);\n"
        "const e = rows.find(r => r.employee_id === j.employee_id);\n"
        "if (!e) return [{ json: { ...j, result: { error: 'EMPLOYEE_NOT_FOUND' } } }];\n"
        "const roles = String(e.it_roles || '').split(';').map(s => s.trim()).filter(Boolean);\n"
        "return [{ json: { ...j, result: { current_access: roles } } }];\n"
    ),
    "get_system_catalog": (
        "const j = $('Gate Check').first().json;\n"
        "const rows = $input.all().map(i => i.json).filter(r => r && r.system_id);\n"
        "const q = (j.payload.system_id || j.payload.query || '').toLowerCase();\n"
        "const hit = rows.filter(r => !q || r.system_id.toLowerCase().includes(q)\n"
        "  || String(r.name_ar).includes(j.payload.system_id || j.payload.query || '')\n"
        "  || String(r.name_en).toLowerCase().includes(q));\n"
        "return [{ json: { ...j, result: { systems: hit.map(r => ({\n"
        "  system_id: r.system_id, name_ar: r.name_ar, name_en: r.name_en,\n"
        "  sensitivity: r.sensitivity, allowed_roles: String(r.allowed_roles || '').split(';').filter(Boolean),\n"
        "})) } } }];\n"
    ),
    "check_leave_overlap": (
        WORKDAY_JS +
        "const j = $('Gate Check').first().json;\n"
        "const txns = $input.all().map(i => i.json);\n"
        "const emps = $('Read Employees (overlap)').all().map(i => i.json);\n"
        "const me = emps.find(r => r.employee_id === j.employee_id) || {};\n"
        "const team = emps.filter(r => r.department === me.department && r.employee_id !== j.employee_id)\n"
        "  .map(r => r.employee_id);\n"
        "const s = j.payload.start_date, e = j.payload.end_date;\n"
        "const overlaps = [];\n"
        "for (const t of txns) {\n"
        "  if (t.skill_id !== 'leave-request') continue;\n"
        "  if (!['awaiting_manager', 'executed'].includes(t.status)) continue;\n"
        "  if (!team.includes(t.employee_id)) continue;\n"
        "  try {\n"
        "    const pl = JSON.parse(t.payload_json || '{}');\n"
        "    if (pl.start_date <= e && pl.end_date >= s) overlaps.push({ employee: t.employee_name,\n"
        "      start_date: pl.start_date, end_date: pl.end_date, status: t.status });\n"
        "  } catch (er) {}\n"
        "}\n"
        "return [{ json: { ...j, result: { requested_working_days: workingDays(s, e),\n"
        "  team_overlaps: overlaps } } }];\n"
    ),
    "read_memory": (
        "const j = $('Gate Check').first().json;\n"
        "const rows = $input.all().map(i => i.json).filter(r => r && r.memory_id);\n"
        "const mine = rows.filter(r => r.status === 'active' && (r.scope === 'org'\n"
        "  || (r.scope === 'employee' && r.subject_id === j.employee_id)));\n"
        "return [{ json: { ...j, result: { memories: mine.map(m => ({\n"
        "  memory_id: m.memory_id, scope: m.scope, content: m.content })) } } }];\n"
    ),
    "write_memory": (
        "const j = $('Gate Check').first().json;\n"
        "const LIMIT = 2200;  // characters, model-independent - the whole GC policy\n"
        "const rows = $input.all().map(i => i.json).filter(r => r && r.memory_id);\n"
        "const p = j.payload || {};\n"
        "const scope = p.scope === 'org' ? 'org' : 'employee';\n"
        "const subject = scope === 'org' ? '' : (p.subject_id || j.employee_id);\n"
        "const scoped = rows.filter(r => r.status === 'active' && r.scope === scope\n"
        "  && (scope === 'org' || r.subject_id === subject));\n"
        "const used = scoped.reduce((n, r) => n + String(r.content || '').length, 0);\n"
        "const action = p.action || 'add';\n"
        "const now = new Date().toISOString();\n"
        "if (action === 'remove' || action === 'replace') {\n"
        "  const target = scoped.find(r => r.memory_id === p.memory_id\n"
        "    || (p.match && String(r.content || '').includes(p.match)));\n"
        "  if (!target) return [{ json: { ...j, result: { error: 'MEMORY_NOT_FOUND' } } }];\n"
        "  const row = { ...target, updated_at: now };\n"
        "  if (action === 'remove') { row.status = 'retired'; }\n"
        "  else { row.content = String(p.content || '').slice(0, 400); }\n"
        "  return [{ json: { ...j, memory_row: row,\n"
        "    result: { ok: true, action, memory_id: row.memory_id } } }];\n"
        "}\n"
        "const content = String(p.content || '').trim().slice(0, 400);\n"
        "if (!content) return [{ json: { ...j, result: { error: 'EMPTY_CONTENT' } } }];\n"
        "if (scoped.some(r => r.content === content))\n"
        "  return [{ json: { ...j, result: { ok: true, deduped: true } } }];\n"
        "if (used + content.length > LIMIT) {\n"
        "  return [{ json: { ...j, result: { error: 'MEMORY_BUDGET_EXCEEDED',\n"
        "    usage: used + '/' + LIMIT,\n"
        "    message: 'الذاكرة ممتلئة. ادمج مدخلات متداخلة أو احذف الأقل أهمية من القائمة ثم أعد المحاولة في الدور نفسه.',\n"
        "    current_entries: scoped.map(r => ({ memory_id: r.memory_id, content: r.content }))\n"
        "  } } }];\n"
        "}\n"
        "const row = { memory_id: 'MEM-' + Date.now(), scope, subject_id: subject,\n"
        "  content, source: p.source || 'reflection', status: 'active', use_count: '0',\n"
        "  created_at: now, updated_at: now };\n"
        "return [{ json: { ...j, memory_row: row, result: { ok: true, action: 'add',\n"
        "  memory_id: row.memory_id, usage: (used + content.length) + '/' + LIMIT } } }];\n"
    ),
    "propose_skill_patch": (
        "const j = $('Gate Check').first().json;\n"
        "const p = j.payload || {};\n"
        "const now = new Date().toISOString();\n"
        "const text = String(p.proposed_text || '').trim().slice(0, 600);\n"
        "if (!text || !p.skill_id)\n"
        "  return [{ json: { ...j, result: { error: 'SKILL_ID_AND_TEXT_REQUIRED' } } }];\n"
        "const rows = $input.all().map(i => i.json).filter(r => r && r.patch_id);\n"
        "if (rows.some(r => r.status === 'pending' && r.skill_id === p.skill_id\n"
        "  && r.proposed_text === text))\n"
        "  return [{ json: { ...j, result: { ok: true, deduped: true } } }];\n"
        "const row = { patch_id: 'PATCH-' + Date.now(), skill_id: p.skill_id,\n"
        "  kind: p.kind || 'add_rule', proposed_text: text,\n"
        "  rationale: String(p.rationale || '').slice(0, 400),\n"
        "  evidence: String(p.evidence || '').slice(0, 200), status: 'pending',\n"
        "  created_by: 'agent', reviewed_by: '', review_note: '',\n"
        "  created_at: now, updated_at: now };\n"
        "return [{ json: { ...j, patch_row: row, result: { ok: true, patch_id: row.patch_id,\n"
        "  status: 'pending', message: 'اقتراح مسجّل بانتظار اعتماد مالك الإجراء' } } }];\n"
    ),
    "submit_transaction": (
        "const j = $('Gate Check').first().json;\n"
        "const emps = $input.all().map(i => i.json);\n"
        "const me = emps.find(r => r.employee_id === j.employee_id) || {};\n"
        "const now = new Date();\n"
        "const txn_id = 'TXN-' + now.getTime();\n"
        "const meta = j.skill_meta || { approval_chain: ['manager'], auto_execute: false, sla_hours: 48 };\n"
        "const chain = meta.approval_chain || []; // governed chain ONLY - never from the model\n"
        "for (const k of Object.keys(j.payload)) if (k.startsWith('_')) delete j.payload[k];\n"
        "const auto = chain.length === 0; // empty chain = instant execution\n"
        "let output_ref = '';\n"
        "if (auto && j.skill_id === 'salary-certificate') output_ref = 'CERT-' + String(now.getTime()).slice(-6);\n"
        "const status = auto ? 'executed' : 'awaiting_' + chain[0];\n"
        "const row = {\n"
        "  txn_id, ts: now.toISOString(), employee_id: j.employee_id,\n"
        "  employee_name: me.name_ar || j.employee_id, skill_id: j.skill_id,\n"
        "  type_ar: meta.title_ar || j.skill_id,\n"
        "  payload_json: JSON.stringify(j.payload), status,\n"
        "  approval_chain: chain.join(';'), chain_pos: 0,\n"
        "  current_approver: chain[0] || '', decision_note: '', output_ref,\n"
        "  sla_hours: meta.sla_hours || 48, updated_at: now.toISOString(),\n"
        "};\n"
        "return [{ json: { ...j, txn_row: row, result: { txn_id, status, output_ref,\n"
        "  approval_chain: chain, message: auto ? 'نُفّذت المعاملة فورًا' : 'أُرسلت لسلسلة الاعتماد' } } }];\n"
    ),
}


def build_gateway():
    wf = Wf("مُنجِز — 02 Service Gateway (sub)")
    trig = wf.add(node("Gateway Input", "n8n-nodes-base.executeWorkflowTrigger", 1.1, (-1200, 0),
                       {"inputSource": "workflowInputs",
                        "workflowInputs": {"values": [
                            {"name": "service", "type": "string"},
                            {"name": "payload", "type": "string"},
                            {"name": "skill_id", "type": "string"},
                            {"name": "employee_id", "type": "string"},
                            {"name": "session_id", "type": "string"}]}}))
    fetch = wf.add(dt_read("Load Skills (gate)", "Skills", (-980, 0)))
    wf.link(trig, fetch)
    gate = wf.add(code("Gate Check", GATE_CHECK_JS, (-760, 0)))
    wf.link(fetch, gate)

    dn = wf.add(if_node("Denied?", "={{ $json.denied }}", "boolean", "true", "true", (-540, 0), single=True))
    wf.link(gate, dn)
    deny_res = wf.add(code("Denied Result", (
        "return [{ json: { ...$json, result: { error: 'SERVICE_DENIED_BY_GOVERNANCE',\n"
        "  message: 'هذه الخدمة غير مصرح بها لهذه المهارة وفق السجل المعتمد.',\n"
        "  allowed_services: $json.allowed_services } } }];\n"
    ), (-320, -220)))
    wf.link(dn, deny_res, output=0)

    services = list(SVC_CODES.keys())
    sw_node = switch_rules("Service Switch", "={{ $json.service }}", services, (-320, 60))
    sw_node["parameters"]["options"] = {"fallbackOutput": "extra"}
    sw = wf.add(sw_node)
    wf.link(dn, sw, output=1)
    ni = wf.add(code("svc: not_implemented", (
        "return [{ json: { ...$json, result: { error: 'SERVICE_NOT_IMPLEMENTED',\n"
        "  message: 'الخدمة مسموحة في المهارة لكنها غير مبنية في البوابة بعد - أبلغ الموظف بذلك.',\n"
        "  service: $json.service } } }];\n"
    ), (-60, 60 + 170 * len(SVC_CODES))))
    wf.link(sw, ni, output=len(services))

    # per-service reads + code
    y = -320
    ends = [deny_res]
    reads_map = {
        "get_employee_profile": [("Read Employees (profile)", "Employees")],
        "get_leave_balance": [("Read LeaveBalances (svc)", "LeaveBalances")],
        "get_salary_record": [("Read Employees (salary)", "Employees"), ("Read Transactions (salary)", "Transactions")],
        "get_expense_policy": [("Read Transactions (policy)", "Transactions"), ("Read ExpensePolicy (svc)", "ExpensePolicy")],
        "get_it_roles": [("Read Employees (roles)", "Employees")],
        "get_system_catalog": [("Read SystemCatalog (svc)", "SystemCatalog")],
        "check_leave_overlap": [("Read Employees (overlap)", "Employees"), ("Read Transactions (overlap)", "Transactions")],
        "submit_transaction": [("Read Employees (submit)", "Employees")],
        "read_memory": [("Read Memory (svc)", "Memory")],
        "write_memory": [("Read Memory (write)", "Memory")],
        "propose_skill_patch": [("Read SkillPatches (svc)", "SkillPatches")],
    }
    for i, svc in enumerate(services):
        x = -60
        prev = None
        for rname, tab in reads_map[svc]:
            n = wf.add(dt_read(rname, tab, (x, y)))
            if prev is None:
                wf.link(sw, n, output=i)
            else:
                wf.link(prev, n)
            prev = n
            x += 220
        c = wf.add(code("svc: " + svc, SVC_CODES[svc], (x, y)))
        wf.link(prev, c)
        ends.append(c)
        y += 170

    # submit path also appends the transaction row
    mem_emit = wf.add(code("Emit Memory Row", (
        "const j = $('svc: write_memory').first().json;\n"
        "return j.memory_row ? [{ json: j.memory_row }] : [];\n"
    ), (720, y - 510), alwaysOutputData=True))
    mem_save = wf.add(dt_upsert("Save Memory", "Memory", "memory_id", (940, y - 510)))
    mem_back = wf.add(code("Carry Memory Result",
                           "return [{ json: $('svc: write_memory').first().json }];", (1160, y - 510)))
    wf.link("svc: write_memory", mem_emit)
    wf.link(mem_emit, mem_save)
    wf.link(mem_save, mem_back)

    pat_emit = wf.add(code("Emit Patch Row", (
        "const j = $('svc: propose_skill_patch').first().json;\n"
        "return j.patch_row ? [{ json: j.patch_row }] : [];\n"
    ), (720, y - 340), alwaysOutputData=True))
    pat_save = wf.add(dt_insert("Save Skill Patch", "SkillPatches", (940, y - 340)))
    pat_back = wf.add(code("Carry Patch Result",
                           "return [{ json: $('svc: propose_skill_patch').first().json }];", (1160, y - 340)))
    wf.link("svc: propose_skill_patch", pat_emit)
    wf.link(pat_emit, pat_save)
    wf.link(pat_save, pat_back)

    tx_emit = wf.add(code("Emit Txn Row", "return [{ json: $json.txn_row }];", (720, y - 170)))
    tx_append = wf.add(dt_insert("Append Transaction", "Transactions", (940, y - 170)))
    tx_back = wf.add(code("Carry Submit Result",
                          "return [{ json: $('svc: submit_transaction').first().json }];", (1160, y - 170)))
    wf.link("svc: submit_transaction", tx_emit)
    wf.link(tx_emit, tx_append)
    wf.link(tx_append, tx_back)
    ends[-1] = tx_back  # submit's end is after the append
    # the two writing learning services must be audited AFTER their row is stored
    for nm, carrier in (("svc: write_memory", mem_back), ("svc: propose_skill_patch", pat_back)):
        ends[ends.index(nm)] = carrier

    ends.append(ni)
    audit_row = wf.add(code("Build Audit Row", (
        "const j = $json;\n"
        "return [{ json: {\n"
        "  ts: new Date().toISOString(), session_id: j.session_id || '',\n"
        "  employee_id: j.employee_id || '', skill_id: j.skill_id || '',\n"
        "  service: j.service || '', request_json: JSON.stringify(j.payload || {}),\n"
        "  result_summary: (j.result && j.result.error) ? ('DENIED/ERROR: ' + j.result.error)\n"
        "    : ('OK ' + JSON.stringify(j.result || {}).slice(0, 160)),\n"
        "} }];\n"
    ), (1400, 60)))
    for e in ends:
        wf.link(e, audit_row)
    audit_append = wf.add(dt_insert("Append AuditLog", "AuditLog", (1620, 60)))
    wf.link(audit_row, audit_append)
    ret = wf.add(code("Return Result", (
        "const src = $('Build Audit Row').first().json;\n"
        "// find the full item that produced the audit row\n"
        "let full = null;\n"
        "for (const n of ['Denied Result','svc: get_employee_profile','svc: get_leave_balance',\n"
        "  'svc: get_salary_record','svc: get_expense_policy','svc: get_it_roles',\n"
        "  'svc: get_system_catalog','svc: check_leave_overlap','Carry Submit Result',\n"
        "  'Carry Memory Result','Carry Patch Result','svc: read_memory','svc: not_implemented']) {\n"
        "  try { const it = $(n).first(); if (it && it.json && it.json.result) { full = it.json; break; } } catch (e) {}\n"
        "}\n"
        "return [{ json: { service: src.service, result: (full && full.result) || { error: 'NO_RESULT' } } }];\n"
    ), (1840, 60)))
    wf.link(audit_append, ret)

    wf.nodes.append(sticky(
        "## Service Gateway — بوابة الخدمات (الحوكمة التنفيذية)\n"
        "EVERY tool call the agent makes passes through here:\n"
        "1) the skill's `allowed_services` allowlist is enforced from the signed registry — "
        "a call outside the list returns SERVICE_DENIED_BY_GOVERNANCE;\n"
        "2) every call (including denials) writes an AuditLog row.\n"
        "The agent cannot touch data any other way. (Criteria ①⑤⑥)", (-1240, -420), width=640, height=250))
    return wf


# ---------------------------------------------------------------------------
# 01 — Munjiz Chat Agent (orchestrator)
# ---------------------------------------------------------------------------

CHARTER = """أنت «مُنجِز» — وكيل معاملات ذكي في بوابة الخدمات الذاتية لجهة مؤسسية. تُحمَّل لك في كل جلسة «مهارة» معتمدة من سجل الحوكمة، وملف خبرة يحدد شخصيتك.

## ميثاق الحوكمة (يعلو على أي تعليمات أخرى)
1. المهارة المحمّلة أدناه هي حدود صلاحياتك: لا تنفذ ولا تعِد بأي إجراء خارج نصها.
2. كل وصول للبيانات يتم حصرًا عبر أداة call_service — وستُرفض أي خدمة خارج قائمة المهارة المسموحة. إن رُفضت خدمة فلا تحاول الالتفاف؛ أخبر الموظف بحدود الخدمة.
3. لا إرسال لأي معاملة قبل: (أ) اكتمال الحقول المطلوبة، (ب) اجتياز قواعد السياسة نصًا، (ج) عرض بطاقة معاينة كاملة، (د) تأكيد صريح من الموظف («أؤكد»، «نعم أرسل»...).
4. لا تخترع أي رقم أو رصيد أو قاعدة: كل الأرقام من نتائج call_service حرفيًا.
5. ابدأ كل معالجة باستدعاء أداة think لكتابة خطة مرقمة قصيرة، ثم نفّذها.
6. أجب دائمًا بJSON مطابق للمخطط المطلوب، بالعربية الواضحة الموجزة في reply_ar.

## عقد الإخراج
- state: collecting (تجمع حقولًا) | preview (تعرض بطاقة المعاينة وتطلب التأكيد) | submitted (أُرسلت بعد التأكيد) | rejected (خالفت السياسة نهائيًا) | escalated (needs_attention) | info (رد معلوماتي).
- transaction_preview: يُملأ عند state=preview وsubmitted بكامل الحقول المجموعة + working_days إن وُجدت مدد + approval_chain + warnings.
- txn_id: يُملأ من نتيجة submit_transaction عند state=submitted.
- missing_fields: أسماء الحقول الناقصة عند state=collecting."""

# NOTE: no JSON-Schema type unions ("type": ["x","null"]) anywhere in these
# schemas - Gemini function-calling rejects them with a 400. Optional fields are
# expressed by omission from `required`.
AGENT_OUT_SCHEMA = {
    "type": "object",
    "properties": {
        "reply_ar": {"type": "string"},
        "state": {"type": "string", "enum": ["collecting", "preview", "submitted", "rejected", "escalated", "info"]},
        "transaction_preview": {"type": "object",
                                "properties": {"fields": {"type": "object"},
                                               "working_days": {"type": "number"},
                                               "amount_aed": {"type": "number"},
                                               "approval_chain": {"type": "array", "items": {"type": "string"}},
                                               "warnings": {"type": "array", "items": {"type": "string"}}}},
        "txn_id": {"type": "string"},
        "missing_fields": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["reply_ar", "state"],
}

ROUTER_JS = (
    "const b = $('Chat Webhook').first().json.body || {};\n"
    "// the skill library is a data table now, so the agent's own improvements are live\n"
    "const index = { skills: (($('Load Skills').first().json.rows) || []).map(r => ({\n"
    "  id: r.skill_id, version: r.version, status: r.status, title_ar: r.title_ar,\n"
    "  title_en: r.title_en, keywords: String(r.keywords || '').split(';').filter(Boolean),\n"
    "  profile_id: r.profile_id, internal: String(r.internal) === 'true',\n"
    "  allowed_services: String(r.allowed_services || '').split(';').filter(Boolean),\n"
    "  approval_chain: String(r.approval_chain || '').split(';').filter(Boolean),\n"
    "  auto_execute: String(r.auto_execute) === 'true', sla_hours: Number(r.sla_hours) || 48,\n"
    "  body_md: r.body_md })) };\n"
    "const skills = (index.skills || []).filter(s => s.status === 'approved' && !s.internal);\n"
    "const listing = skills.map(s => ({ id: s.id, title_ar: s.title_ar, keywords: s.keywords }));\n"
    "const prompt = ['أنت مصنّف نوايا لبوابة خدمات موظفين. طلب الموظف:', b.message || '',\n"
    "  'المهارات المتاحة:', JSON.stringify(listing),\n"
    "  'أعد JSON فقط: {\"skill_id\": \"<id أو null>\", \"confidence\": 0..1}. اختر null إذا لم يطابق الطلب أي مهارة بوضوح.'].join('\\n');\n"
    "return [{ json: {\n"
    "  employee_id: b.employee_id || '', session_id: b.session_id || ('S-' + Date.now()),\n"
    "  message: b.message || '', active_skill_id: b.active_skill_id || '',\n"
    "  skills, listing,\n"
    "  geminiBody: { contents: [{ role: 'user', parts: [{ text: prompt }] }],\n"
    "    generationConfig: { temperature: 0, response_mime_type: 'application/json' } },\n"
    "} }];\n"
)

PICK_SKILL_JS = (
    "const prep = $('Prepare Router').first().json;\n"
    "let skill_id = prep.active_skill_id || '';\n"
    "let confidence = 1;\n"
    "if (!skill_id) {\n"
    "  const r = $json.gemini_json || {};\n"
    "  skill_id = r.skill_id && r.skill_id !== 'null' ? r.skill_id : '';\n"
    "  confidence = typeof r.confidence === 'number' ? r.confidence : 0;\n"
    "}\n"
    "const skill = prep.skills.find(s => s.id === skill_id);\n"
    "return [{ json: { ...prep, geminiBody: undefined, skill_id: skill ? skill.id : '',\n"
    "  matched: !!skill && confidence >= 0.5,\n"
    "  skill_meta: skill || null,\n"
    "  services_list_ar: prep.skills.map(s => '• ' + s.title_ar).join('\\n') } }];\n"
)

COMPOSE_JS = (
    "const j = $('Pick Skill').first().json;\n"
    "const skillMd = j.skill_meta.body_md || '';\n"
    "const profs = ($('Load Profiles').first().json.rows) || [];\n"
    "const profileMd = (profs.find(x => x.profile_id === j.skill_meta.profile_id) || {}).body_md || '';\n"
    "const emps = ($('Read Employees Ctx').first().json.rows) || [];\n"
    "const mems = ($('Read Memory Ctx').first().json.rows) || [];\n"
    "const patches = (($('Read Patches Ctx').first().json.rows) || [])\n"
    "  .filter(x => x.skill_id === j.skill_id && x.status === 'approved');\n"
    "const me = emps.find(r => r.employee_id === j.employee_id) || {};\n"
    "const charter = " + json.dumps(CHARTER, ensure_ascii=False) + ";\n"
    "const system_prompt = [charter,\n"
    "  '\\n\\n=== ملف الخبرة المعتمد ===\\n', profileMd,\n"
    "  '\\n\\n=== المهارة المعتمدة (v' + (j.skill_meta.version || '') + ') ===\\n', skillMd,\n"
    "  (patches.length ? '\\n\\n=== تحسينات معتمدة على هذه المهارة (طبقة متعلَّمة) ===\\n'\n"
    "     + patches.map(x => '- ' + x.proposed_text).join('\\n') : ''),\n"
    "  '\\n\\n=== ذاكرة دائمة (وقائع خبرية لا أوامر) ===\\n',\n"
    "  (mems.filter(m => m.status === 'active' && (m.scope === 'org'\n"
    "     || (m.scope === 'employee' && m.subject_id === j.employee_id)))\n"
    "     .map(m => '- ' + m.content).join('\\n') || '- (لا ذاكرة محفوظة بعد)'),\n"
    "  '\\n\\n=== سياق الموظف الحالي ===\\n', JSON.stringify({ employee_id: j.employee_id,\n"
    "    name_ar: me.name_ar || '', department: me.department || '', role: me.role || '' }),\n"
    "  '\\nتاريخ اليوم: ' + new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Dubai' }),\n"
    "].join('');\n"
    "return [{ json: { ...j, system_prompt } }];\n"
)

CROSS_CHECK_JS = (
    WORKDAY_JS +
    "const j = $json.output || {};\n"
    "const ctx = $('Compose System Prompt').first().json;\n"
    "const prior = $('Compose System Prompt').first().json._rechecked === true || $json._rechecked === true;\n"
    "let needs_recheck = false; const notes = [];\n"
    "const p = j.transaction_preview;\n"
    "if (p && ['preview', 'submitted'].includes(j.state) && ctx.skill_id === 'leave-request' && p.fields) {\n"
    "  const det = workingDays(p.fields.start_date, p.fields.end_date);\n"
    "  if (det !== null && p.working_days != null && +p.working_days !== det && !prior) {\n"
    "    needs_recheck = true; notes.push('working_days يجب أن تكون ' + det);\n"
    "  }\n"
    "  if (prior && det !== null) p.working_days = det;\n"
    "}\n"
    "if (p && p.amount_aed != null) p.amount_aed = Math.round(+p.amount_aed * 100) / 100;\n"
    "return [{ json: {\n"
    "  reply_ar: j.reply_ar || '', state: j.state || 'info',\n"
    "  transaction_preview: p || null, txn_id: j.txn_id || null,\n"
    "  missing_fields: j.missing_fields || [],\n"
    "  skill_id: ctx.skill_id, session_id: ctx.session_id,\n"
    "  needs_recheck, recheck_notes: notes, _rechecked: prior,\n"
    "} }];\n"
)

RE_REASON_JS = (
    "const j = $json;\n"
    "const prompt = ['راجع ردك: المدقق الحتمي وجد خطأً حسابيًا.', j.recheck_notes.join('؛ '),\n"
    "  'ردك السابق:', JSON.stringify({ reply_ar: j.reply_ar, state: j.state,\n"
    "    transaction_preview: j.transaction_preview, missing_fields: j.missing_fields }),\n"
    "  'صحّح الأرقام وأعد JSON بنفس المخطط تمامًا دون أي نص آخر.'].join('\\n');\n"
    "return [{ json: { ...j, geminiBody: { contents: [{ role: 'user', parts: [{ text: prompt }] }],\n"
    "  generationConfig: { temperature: 0, response_mime_type: 'application/json' } } } }];\n"
)


def build_agent():
    wf = Wf("مُنجِز — 01 Chat Agent")
    hook = wf.add(node("Chat Webhook", "n8n-nodes-base.webhook", 2, (-1700, 0),
                       {"httpMethod": "POST", "path": "munjiz/chat",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    fetch_idx = wf.add(exec_wf("Load Skills", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                               {"action": "read", "tab": "Skills"}, (-1480, 0)))
    wf.link(hook, fetch_idx)
    prep = wf.add(code("Prepare Router", ROUTER_JS, (-1260, 0)))
    wf.link(fetch_idx, prep)

    has_active = wf.add(if_node("Has Active Skill?", "={{ $json.active_skill_id }}", "string",
                                "notEmpty", "", (-1040, 0), single=True))
    wf.link(prep, has_active)
    router = wf.add(gemini("Gemini: Route Intent", (-1040, 220)))
    wf.link(has_active, router, output=1)
    rparse = wf.add(code("Parse Route", GPARSE, (-820, 220)))
    wf.link(router, rparse)
    pick = wf.add(code("Pick Skill", PICK_SKILL_JS, (-600, 110)))
    wf.link(has_active, pick, output=0)
    wf.link(rparse, pick)

    matched = wf.add(if_node("Matched?", "={{ $json.matched }}", "boolean", "true", "true", (-380, 110), single=True))
    wf.link(pick, matched)
    no_match = wf.add(respond("Respond: Services List",
        '={{ { "reply": "أهلًا بك في مُنجِز 👋 لم أتبيّن الخدمة المطلوبة. الخدمات المتاحة حاليًا:\\n" + $json.services_list_ar + "\\nأخبرني أيّها تريد.", "state": "info", "skill_id": "", "session_id": $json.session_id } }}',
        (-160, 320)))
    wf.link(matched, no_match, output=1)

    f_skill = wf.add(node("Skill Body", "n8n-nodes-base.noOp", 1, (-160, 0), {}))
    wf.link(matched, f_skill, output=0)
    f_prof = wf.add(exec_wf("Load Profiles", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                            {"action": "read", "tab": "Profiles"}, (60, 0)))
    wf.link(f_skill, f_prof)
    emp_read = wf.add(exec_wf("Read Employees Ctx", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                              {"action": "read", "tab": "Employees"}, (280, 0)))
    mem_read = wf.add(exec_wf("Read Memory Ctx", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                              {"action": "read", "tab": "Memory"}, (390, 0)))
    pat_read = wf.add(exec_wf("Read Patches Ctx", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                              {"action": "read", "tab": "SkillPatches"}, (450, 0)))
    wf.link(f_prof, emp_read)
    wf.link(emp_read, mem_read)
    wf.link(mem_read, pat_read)
    compose = wf.add(code("Compose System Prompt", COMPOSE_JS, (500, 0)))
    wf.link(pat_read, compose)

    agent = wf.add(node("Munjiz Agent", "@n8n/n8n-nodes-langchain.agent", 2.2, (760, 0),
                        {"promptType": "define",
                         "text": "={{ $json.message }}",
                         "hasOutputParser": True,
                         "options": {"systemMessage": "={{ $json.system_prompt }}",
                                     "maxIterations": 10, "returnIntermediateSteps": True}},
                        retryOnFail=True, maxTries=3, waitBetweenTries=15000))
    lm = wf.add(node("Gemini Chat Model", "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", 1, (620, 260),
                     {"modelName": "models/" + MODEL_MAIN, "options": {"temperature": 0.2}},
                     credentials=CRED_GEMINI))
    wf.link(lm, agent, ctype="ai_languageModel")
    mem = wf.add(node("Session Memory", "@n8n/n8n-nodes-langchain.memoryBufferWindow", 1.3, (780, 260),
                      {"sessionIdType": "customKey",
                       "sessionKey": "={{ $('Pick Skill').first().json.session_id }}",
                       "contextWindowLength": 12}))
    wf.link(mem, agent, ctype="ai_memory")
    parser = wf.add(node("Structured Output", "@n8n/n8n-nodes-langchain.outputParserStructured", 1.2, (940, 260),
                         {"schemaType": "manual",
                          "inputSchema": json.dumps(AGENT_OUT_SCHEMA, ensure_ascii=False, indent=2)}))
    wf.link(parser, agent, ctype="ai_outputParser")
    think = wf.add(node("think", "@n8n/n8n-nodes-langchain.toolThink", 1, (1100, 260), {}))
    wf.link(think, agent, ctype="ai_tool")
    call_svc = wf.add(node("call_service", "@n8n/n8n-nodes-langchain.toolWorkflow", 2.2, (1260, 260),
                           {"name": "call_service",
                            "description": ("بوابة الخدمات الموحدة والوحيدة للبيانات والمعاملات. "
                                            "أرسل service (اسم الخدمة كما في المهارة) وpayload (JSON string). "
                                            "الخدمات خارج قائمة المهارة سترفضها الحوكمة. "
                                            "أمثلة: get_employee_profile بلا payload؛ "
                                            "get_leave_balance بلا payload؛ "
                                            "check_leave_overlap بـ {\"start_date\",\"end_date\"}؛ "
                                            "submit_transaction بكامل حقول المعاملة."),
                            "source": "database",
                            "workflowId": wfref(GATEWAY_ID, "مُنجِز — 02 Service Gateway (sub)"),
                            "workflowInputs": {"mappingMode": "defineBelow", "value": {
                                "service": "={{ $fromAI('service', 'service name from the skill allowed_services', 'string') }}",
                                "payload": "={{ $fromAI('payload', 'JSON string of the service payload, or empty', 'string') }}",
                                "skill_id": "={{ $('Pick Skill').first().json.skill_id }}",
                                "employee_id": "={{ $('Pick Skill').first().json.employee_id }}",
                                "session_id": "={{ $('Pick Skill').first().json.session_id }}",
                            }, "matchingColumns": [], "schema": [],
                                "attemptToConvertTypes": False, "convertFieldsToString": False}}))
    wf.link(call_svc, agent, ctype="ai_tool")
    wf.link(compose, agent)

    cross = wf.add(code("Deterministic Cross-Check", CROSS_CHECK_JS, (1020, 0)))
    wf.link(agent, cross)
    needs = wf.add(if_node("Needs Re-reason?", "={{ $json.needs_recheck }}", "boolean", "true", "true",
                           (1240, 0), single=True))
    wf.link(cross, needs)
    rr = wf.add(code("Build Re-reason", RE_REASON_JS, (1240, -220)))
    rr_call = wf.add(gemini("Gemini: Re-reason", (1460, -220)))
    rr_parse = wf.add(code("Parse Re-reason", GPARSE, (1680, -220)))
    rr_merge = wf.add(code("Merge Re-reason", (
        "const prev = $('Deterministic Cross-Check').first().json;\n"
        "const fixed = $json.gemini_ok ? $json.gemini_json : {\n"
        "  reply_ar: prev.reply_ar, state: prev.state, transaction_preview: prev.transaction_preview,\n"
        "  txn_id: prev.txn_id, missing_fields: prev.missing_fields };\n"
        "return [{ json: { output: fixed, _rechecked: true } }];\n"
    ), (1900, -220)))
    wf.link(needs, rr, output=0)
    wf.link(rr, rr_call)
    wf.link(rr_call, rr_parse)
    wf.link(rr_parse, rr_merge)
    wf.link(rr_merge, cross)

    resp = wf.add(respond("Respond Chat",
        '={{ { "reply": $json.reply_ar, "state": $json.state, "preview": $json.transaction_preview, "txn_id": $json.txn_id, "missing_fields": $json.missing_fields, "skill_id": $json.skill_id, "session_id": $json.session_id } }}',
        (1460, 60)))
    wf.link(needs, resp, output=1)

    wf.nodes.append(sticky(
        "## مُنجِز — Chat Agent (criteria ①②③④⑤⑥)\n"
        "④ webhook trigger from the portal. ⑤ router picks the SKILL at runtime; the whole "
        "system prompt is composed dynamically from GitHub (governed SKILL.md + PROFILE.md). "
        "① one governed tool (call_service) — the model chooses WHICH service per step. "
        "② think-tool plan first. ③ session memory + registry sheets. "
        "⑥ deterministic working-day cross-check forces a re-reason pass on mismatch.",
        (-1720, -380), width=700, height=240))
    return wf


# ---------------------------------------------------------------------------
# 03 — Approvals
# ---------------------------------------------------------------------------

DECIDE_JS = (
    WORKDAY_JS +
    "const b = $json.body || {};\n"
    "const txns = $('Read Transactions (decide)').all().map(i => i.json);\n"
    "const emps = $('Read Employees (decide)').all().map(i => i.json);\n"
    "const t = txns.find(r => r.txn_id === b.txn_id);\n"
    "if (!t) return [{ json: { ok: false, error: 'TXN_NOT_FOUND' } }];\n"
    "if (!String(t.status || '').startsWith('awaiting_'))\n"
    "  return [{ json: { ok: false, error: 'NOT_PENDING', status: t.status } }];\n"
    "const stage = t.current_approver;\n"
    "const approver = emps.find(r => r.employee_id === b.approver_id) || {};\n"
    "const owner = emps.find(r => r.employee_id === t.employee_id) || {};\n"
    "// manager stage authorizes ONLY the employee's own manager; other stages match by role\n"
    "const authorized = stage === 'manager' ? (owner.manager_id === b.approver_id)\n"
    "  : (approver.role === stage);\n"
    "if (!authorized) return [{ json: { ok: false, error: 'NOT_AUTHORIZED', stage } }];\n"
    "const dec = String(b.decision || '').toLowerCase();\n"
    "if (dec !== 'approve' && dec !== 'reject') return [{ json: { ok: false, error: 'INVALID_DECISION' } }];\n"
    "const chain = String(t.approval_chain || '').split(';').filter(Boolean);\n"
    "const pos = +t.chain_pos || 0;\n"
    "let update = { txn_id: t.txn_id, decision_note: b.note || '', updated_at: new Date().toISOString() };\n"
    "let side = null;\n"
    "if (dec === 'reject') {\n"
    "  update.status = 'rejected'; update.current_approver = '';\n"
    "} else if (pos + 1 < chain.length) {\n"
    "  update.status = 'awaiting_' + chain[pos + 1];\n"
    "  update.current_approver = chain[pos + 1]; update.chain_pos = pos + 1;\n"
    "} else {\n"
    "  update.status = 'executed'; update.current_approver = ''; update.chain_pos = pos + 1;\n"
    "  let pl = {}; try { pl = JSON.parse(t.payload_json || '{}'); } catch (e) {}\n"
    "  if (t.skill_id === 'leave-request' && pl.start_date && pl.end_date) {\n"
    "    const days = pl.working_days || workingDays(pl.start_date, pl.end_date) || 0;\n"
    "    side = { kind: 'leave', employee_id: t.employee_id, leave_type: pl.leave_type || 'annual', days };\n"
    "  }\n"
    "  if (t.skill_id === 'it-access-request' && pl.system_id) {\n"
    "    side = { kind: 'it', employee_id: t.employee_id, grant: pl.system_id + ':' + (pl.access_level || 'read') };\n"
    "  }\n"
    "}\n"
    "return [{ json: { ok: true, update, side, txn: t, owner_email: owner.email || '',\n"
    "  decision: b.decision, stage } }];\n"
)

SIDE_JS = (
    "const j = $json;\n"
    "if (!j.side) return [];\n"
    "if (j.side.kind === 'leave') {\n"
    "  const bals = $('Read LeaveBalances (side)').all().map(i => i.json);\n"
    "  const b = bals.find(r => r.employee_id === j.side.employee_id);\n"
    "  if (!b) return [];\n"
    "  const field = j.side.leave_type === 'sick' ? 'sick_used' : 'annual_used';\n"
    "  return [{ json: { employee_id: b.employee_id, [field]: +b[field] + j.side.days } }];\n"
    "}\n"
    "if (j.side.kind === 'it') {\n"
    "  const emps = $('Read Employees (side)').all().map(i => i.json);\n"
    "  const e = emps.find(r => r.employee_id === j.side.employee_id);\n"
    "  if (!e) return [];\n"
    "  const roles = String(e.it_roles || '').split(';').filter(Boolean);\n"
    "  if (!roles.includes(j.side.grant)) roles.push(j.side.grant);\n"
    "  return [{ json: { employee_id: e.employee_id, it_roles: roles.join(';') } }];\n"
    "}\n"
    "return [];\n"
)


def build_approvals():
    wf = Wf("مُنجِز — 03 Approvals")
    hook = wf.add(node("Decide Webhook", "n8n-nodes-base.webhook", 2, (-1100, 0),
                       {"httpMethod": "POST", "path": "munjiz/decide",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    r1 = wf.add(dt_read("Read Transactions (decide)", "Transactions", (-880, 0)))
    r2 = wf.add(dt_read("Read Employees (decide)", "Employees", (-660, 0)))
    wf.link(hook, r1)
    wf.link(r1, r2)
    dec = wf.add(code("Decide", DECIDE_JS.replace("const b = $json.body || {};",
                                                  "const b = $('Decide Webhook').first().json.body || {};"),
                      (-440, 0)))
    wf.link(r2, dec)
    ok = wf.add(if_node("OK?", "={{ $json.ok }}", "boolean", "true", "true", (-220, 0), single=True))
    wf.link(dec, ok)
    err = wf.add(respond("Respond Error", '={{ { "ok": false, "error": $json.error } }}', (0, 200)))
    wf.link(ok, err, output=1)

    upd_emit = wf.add(code("Emit Txn Update", "return [{ json: $json.update }];", (0, -80)))
    wf.link(ok, upd_emit, output=0)
    upd = wf.add(dt_upsert("Update Transaction", "Transactions", "txn_id", (220, -80)))
    wf.link(upd_emit, upd)

    r3 = wf.add(dt_read("Read LeaveBalances (side)", "LeaveBalances", (440, -80)))
    r4 = wf.add(dt_read("Read Employees (side)", "Employees", (660, -80)))
    wf.link(upd, r3)
    wf.link(r3, r4)
    side = wf.add(code("Apply Side Effect", SIDE_JS.replace("const j = $json;",
                                                            "const j = $('Decide').first().json;"), (880, -80),
                       alwaysOutputData=True))
    wf.link(r4, side)
    has_side = wf.add(if_node("Leave Side?", "={{ $json.annual_used !== undefined || $json.sick_used !== undefined }}",
                              "boolean", "true", "true", (1100, -80), single=True))
    wf.link(side, has_side)
    up_bal = wf.add(dt_upsert("Update LeaveBalances", "LeaveBalances", "employee_id", (1320, -180)))
    wf.link(has_side, up_bal, output=0)
    has_it = wf.add(if_node("IT Side?", "={{ $json.it_roles !== undefined }}", "boolean", "true", "true",
                            (1320, 0), single=True))
    wf.link(has_side, has_it, output=1)
    up_emp = wf.add(dt_upsert("Update Employee Roles", "Employees", "employee_id", (1540, -60)))
    wf.link(has_it, up_emp, output=0)
    conv = wf.add(node("Converge", "n8n-nodes-base.noOp", 1, (1540, 120), {}))
    wf.link(has_it, conv, output=1)
    wf.link(up_bal, conv)
    wf.link(up_emp, conv)

    notify = wf.add(code("Build Notification", (
        "const d = $('Decide').first().json;\n"
        "return [{ json: {\n"
        "  ts: new Date().toISOString(), session_id: 'approvals',\n"
        "  employee_id: d.txn.employee_id, skill_id: d.txn.skill_id,\n"
        "  service: 'notify_employee',\n"
        "  request_json: JSON.stringify({ txn_id: d.txn.txn_id, decision: d.decision }),\n"
        "  result_summary: 'حالة معاملتك (' + d.txn.type_ar + ') أصبحت: ' + d.update.status\n"
        "    + (d.update.decision_note ? ' — ملاحظة: ' + d.update.decision_note : ''),\n"
        "} }];\n"
    ), (1760, 120)))
    mail = wf.add(dt_insert("Notify Employee", "AuditLog", (1960, 120)))
    wf.link(conv, notify)
    wf.link(notify, mail)
    resp = wf.add(respond("Respond Decide",
                          '={{ { "ok": true, "status": $(\'Decide\').first().json.update.status } }}', (1980, 120)))
    wf.link(mail, resp)
    wf.nodes.append(sticky(
        "## Approvals — سلسلة الاعتماد\nHuman decisions only: validates the approver "
        "(manager relation or role = stage), advances the chain, applies side effects on final "
        "approval (leave balance deduction / IT role grant), notifies the employee.",
        (-1120, -300), width=620, height=200))
    return wf


# ---------------------------------------------------------------------------
# 04 — SLA Chaser
# ---------------------------------------------------------------------------

CHASER_FIND_JS = (
    "const d = $json;\n"
    "const now = Date.now();\n"
    "const emps = d.employees || [];\n"
    "const byId = {}; for (const e of emps) byId[e.employee_id] = e;\n"
    "const cases = [];\n"
    "for (const t of (d.transactions || [])) {\n"
    "  if (!String(t.status || '').startsWith('awaiting_')) continue;\n"
    "  const ageH = (now - new Date(t.updated_at || t.ts).getTime()) / 36e5;\n"
    "  const sla = +t.sla_hours || 48;\n"
    "  if (ageH < sla * 0.5) continue;\n"
    "  const owner = byId[t.employee_id] || {};\n"
    "  const mgr = byId[owner.manager_id] || {};\n"
    "  cases.push({ txn_id: t.txn_id, type_ar: t.type_ar, employee: t.employee_name,\n"
    "    stage: t.current_approver, age_hours: Math.round(ageH * 10) / 10, sla_hours: sla,\n"
    "    breached: ageH > sla, approver_email: t.current_approver === 'manager' ? (mgr.email || '') : '',\n"
    "  });\n"
    "}\n"
    "return [{ json: { cases, case_count: cases.length, now: new Date().toISOString() } }];\n"
)

CHASER_SCHEMA = {
    "type": "object",
    "properties": {"decisions": {"type": "array", "items": {
        "type": "object",
        "properties": {"txn_id": {"type": "string"},
                       "action": {"type": "string", "enum": ["remind_approver", "escalate", "wait"]},
                       "justification_ar": {"type": "string"}},
        "required": ["txn_id", "action", "justification_ar"]}}},
    "required": ["decisions"],
}


def build_chaser():
    wf = Wf("مُنجِز — 04 SLA Chaser")
    sched = wf.add(node("Every 12 Hours", "n8n-nodes-base.scheduleTrigger", 1.2, (-1100, -120),
                        {"rule": {"interval": [{"field": "hours", "hoursInterval": CHASER_HOURS}]}}))
    manual = wf.add(node("Manual Test", "n8n-nodes-base.manualTrigger", 1, (-1100, 40), {}))
    hook = wf.add(node("Chase Webhook", "n8n-nodes-base.webhook", 2, (-1100, 200),
                       {"httpMethod": "POST", "path": "munjiz/chase",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    ack = wf.add(respond("Respond Chase", '={{ { "ok": true, "fired": true } }}', (-1100, 360)))
    wf.link(hook, ack)
    rd = wf.add(exec_wf("Read All", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                        {"action": "read_all", "tab": ""}, (-860, 40)))
    for t in (sched, manual, ack):
        wf.link(t, rd)
    find = wf.add(code("Find Stale", CHASER_FIND_JS, (-640, 40)))
    wf.link(rd, find)
    any_ = wf.add(if_node("Any Stale?", "={{ $json.case_count }}", "number", "gt", 0, (-420, 40)))
    wf.link(find, any_)
    idle = wf.add(node("Nothing ✓", "n8n-nodes-base.noOp", 1, (-200, 200), {}))
    wf.link(any_, idle, output=1)

    agent = wf.add(node("Chaser Agent", "@n8n/n8n-nodes-langchain.agent", 2.2, (-180, -40),
                        {"promptType": "define",
                         "text": "={{ 'المعاملات المتأخرة عن سلسلة الاعتماد (' + $json.now + '):\\n' + JSON.stringify($json.cases) }}",
                         "hasOutputParser": True,
                         "options": {"systemMessage": (
                             "أنت «حارس الإنجاز» في بوابة مُنجِز. لكل معاملة متأخرة قرر: remind_approver "
                             "(اقتربت من sla ولم تُذكَّر)، escalate (تجاوزت sla — تصعيد للإدارة العليا)، "
                             "أو wait (قريبة العهد). اكتب مسوّغًا عربيًا رسميًا موجزًا لكل قرار — يُحفظ في سجل التدقيق. "
                             "أعد JSON فقط."),
                             "maxIterations": 6, "returnIntermediateSteps": True}},
                        retryOnFail=True, maxTries=3, waitBetweenTries=15000))
    wf.link(any_, agent, output=0)
    lm = wf.add(node("Gemini Chat Model (chaser)", "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", 1, (-300, 180),
                     {"modelName": "models/" + MODEL_CHEAP, "options": {"temperature": 0.2}},
                     credentials=CRED_GEMINI))
    wf.link(lm, agent, ctype="ai_languageModel")
    parser = wf.add(node("Chaser Output", "@n8n/n8n-nodes-langchain.outputParserStructured", 1.2, (-140, 180),
                         {"schemaType": "manual",
                          "inputSchema": json.dumps(CHASER_SCHEMA, ensure_ascii=False, indent=2)}))
    wf.link(parser, agent, ctype="ai_outputParser")

    flat = wf.add(code("Flatten", (
        "const cases = $('Find Stale').first().json.cases;\n"
        "const by = {}; for (const c of cases) by[c.txn_id] = c;\n"
        "const out = [];\n"
        "for (const dd of (($json.output || {}).decisions || [])) {\n"
        "  if (dd.action === 'wait') continue;\n"
        "  out.push({ json: { ...(by[dd.txn_id] || {}), ...dd, ts: new Date().toISOString() } });\n"
        "}\n"
        "return out; // empty = nothing to act on, chain ends here\n"
    ), (80, -40)))
    wf.link(agent, flat)
    # audit BEFORE the sends: one row per decision, immune to Gmail response overwrite
    audit_rows = wf.add(code("Audit Rows", (
        "return $input.all().map(i => ({ json: {\n"
        "  ts: i.json.ts, session_id: 'sla-chaser', employee_id: '',\n"
        "  skill_id: '', service: 'sla_' + i.json.action,\n"
        "  request_json: JSON.stringify({ txn_id: i.json.txn_id, hours_late: i.json.age_hours }),\n"
        "  result_summary: i.json.justification_ar || '' } }));\n"
    ), (300, -40)))
    wf.link(flat, audit_rows)
    logw = wf.add(dt_insert("Append AuditLog (chaser)", "AuditLog", (520, -40)))
    wf.link(audit_rows, logw)
    carry = wf.add(code("Carry Decisions", "return $('Flatten').all();", (740, -40)))
    wf.link(logw, carry)
    act = wf.add(switch_rules("Chaser Switch", "={{ $json.action }}", ["remind_approver", "escalate"], (960, -40)))
    wf.link(carry, act)
    remind = wf.add(node("Remind Approver", "n8n-nodes-base.noOp", 1, (540, -140), {}))
    wf.link(act, remind, output=0)
    esc = wf.add(node("Escalate", "n8n-nodes-base.noOp", 1, (540, 60), {}))
    wf.link(act, esc, output=1)
    wf.nodes.append(sticky(
        "## SLA Chaser — حارس الإنجاز (criteria ④⑤⑥)\nEvery 5 minutes it reads pending "
        "transactions, and the MODEL decides per case: remind / escalate / wait — each decision "
        "logged with its written justification.", (-1120, -320), width=620, height=190))
    return wf


# ---------------------------------------------------------------------------
# 05 — Dashboard API, 06 — Error handler, 07 — Demo reset
# ---------------------------------------------------------------------------

ASSEMBLE_JS = (
    "const d = $json;\n"
    "const index = { skills: (d.skills || []).map(r => ({ id: r.skill_id, version: r.version,\n"
    "  status: r.status, title_ar: r.title_ar, title_en: r.title_en,\n"
    "  internal: String(r.internal) === 'true', created_by: r.created_by, updated_at: r.updated_at,\n"
    "  allowed_services: String(r.allowed_services || '').split(';').filter(Boolean),\n"
    "  approval_chain: String(r.approval_chain || '').split(';').filter(Boolean),\n"
    "  sla_hours: Number(r.sla_hours) || 48 })) };\n"
    "const txns = (d.transactions || []).filter(t => t.txn_id)\n"
    "  .sort((a, b) => String(b.ts).localeCompare(String(a.ts)));\n"
    "const today = new Date().toISOString().slice(0, 10);\n"
    "return [{ json: {\n"
    "  generated_at: new Date().toISOString(),\n"
    "  kpis: {\n"
    "    total: txns.length,\n"
    "    today: txns.filter(t => String(t.ts).startsWith(today)).length,\n"
    "    pending: txns.filter(t => String(t.status).startsWith('awaiting_')).length,\n"
    "    executed: txns.filter(t => t.status === 'executed').length,\n"
    "    rejected: txns.filter(t => t.status === 'rejected').length,\n"
    "    minutes_saved: txns.filter(t => t.status === 'executed').length * 25,\n"
    "  },\n"
    "  transactions: txns.slice(0, 100),\n"
    "  audit: (d.audit || []).slice(-60).reverse(),\n"
    "  skills: (index.skills || []),\n"
    "  memory: (d.memory || []).filter(m => m.status === 'active'),\n"
    "  patches: (d.patches || []).sort((a, b) =>\n"
    "    String(b.created_at).localeCompare(String(a.created_at))),\n"
    "  learning: {\n"
    "    memory_entries: (d.memory || []).filter(m => m.status === 'active').length,\n"
    "    memory_chars: (d.memory || []).filter(m => m.status === 'active')\n"
    "      .reduce((n, m) => n + String(m.content || '').length, 0),\n"
    "    memory_budget: 2200,\n"
    "    pending_patches: (d.patches || []).filter(x => x.status === 'pending').length,\n"
    "    approved_patches: (d.patches || []).filter(x => x.status === 'approved').length,\n"
    "  },\n"
    "  employees: (d.employees || []).map(e => ({ employee_id: e.employee_id, name_ar: e.name_ar,\n"
    "    name_en: e.name_en || '', role: e.role, department: e.department, manager_id: e.manager_id })),\n"
    "  balances: d.balances || [],\n"
    "} }];\n"
)


def build_dash():
    wf = Wf("مُنجِز — 05 Dashboard API")
    hook = wf.add(node("GET State", "n8n-nodes-base.webhook", 2, (-700, 0),
                       {"httpMethod": "GET", "path": "munjiz/state",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    idx = wf.add(node("Dashboard Start", "n8n-nodes-base.noOp", 1, (-480, 0), {}))
    wf.link(hook, idx)
    rd = wf.add(exec_wf("Read All (dash)", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                        {"action": "read_all", "tab": ""}, (-260, 0)))
    wf.link(idx, rd)
    asm = wf.add(code("Assemble Dashboard", ASSEMBLE_JS, (-40, 0)))
    wf.link(rd, asm)
    resp = wf.add(respond("Respond State", "={{ $json }}", (180, 0)))
    wf.link(asm, resp)
    wf.nodes.append(sticky("## Dashboard API\n`GET /munjiz/state` — polled by the portal every 3s. "
                           "Skills come LIVE from the GitHub registry (the live-add demo beat needs "
                           "no n8n change).", (-720, -220), width=560, height=160))
    return wf


def build_error():
    wf = Wf("مُنجِز — 06 Error Handler")
    trig = wf.add(node("Error Trigger", "n8n-nodes-base.errorTrigger", 1, (-500, 0), {}))
    ext = wf.add(code("Extract", (
        "const j = $json;\n"
        "const wfName = (j.workflow || {}).name || '?';\n"
        "const nodeName = (j.execution || {}).lastNodeExecuted || '?';\n"
        "const msg = ((j.execution || {}).error || {}).message || '?';\n"
        "return [{ json: { ts: new Date().toISOString(), session_id: 'error-handler',\n"
        "  employee_id: '', skill_id: '', service: 'workflow_error',\n"
        "  request_json: JSON.stringify({ workflow: wfName, node: nodeName }),\n"
        "  result_summary: msg } }];\n"
    ), (-280, 0)))
    mail = wf.add(dt_insert("Notify", "AuditLog", (-60, 0)))
    done = wf.add(node("Logged ✓", "n8n-nodes-base.noOp", 1, (160, 0), {}))
    wf.link(trig, ext)
    wf.link(ext, mail)
    wf.link(mail, done)
    wf.nodes.append(sticky("## Error Handler (criterion ⑥)\nSet as error workflow for 01/03/04/05.",
                           (-520, -180), width=440, height=120))
    return wf


def build_seed():
    """Provision the datastore inside n8n: create the six data tables, clear them
    and load the synthetic seed. Idempotent, so it doubles as the demo-reset
    button (POST /munjiz/reset). No external service is involved."""
    wf = Wf("مُنجِز — 07 Provision & Seed")
    hook = wf.add(node("POST Reset", "n8n-nodes-base.webhook", 2, (-1000, 0),
                       {"httpMethod": "POST", "path": "munjiz/reset",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    manual = wf.add(node("Seed Manually", "n8n-nodes-base.manualTrigger", 1, (-1000, 220), {}))
    ack = wf.add(respond("Respond Reset", '={{ { "ok": true, "seeded": true } }}', (-780, 0)))
    wf.link(hook, ack)
    prev = None
    x = -520
    for table in build_data.TABS:
        cols = [{"name": c, "type": "string"} for c in build_data.TABS[table][0]]
        lines = ["const rows = JSON.parse(" + js_lit(seed_rows(table)) + ");"]
        if table == "Transactions":
            lines += [
                "const stale = new Date(Date.now() - 30 * 3600 * 1000).toISOString();",
                "// re-arm the SLA anchor relative to now so the chaser always has a live case",
                "for (const r of rows) if (r.txn_id === 'TXN-SEED-CHASE') { r.ts = stale; r.updated_at = stale; }",
            ]
        lines.append("return rows.map(r => ({ json: r }));")
        create = wf.add(node("Create " + table, DT_TYPE, DT_VER, (x, 0), {
            "resource": "table", "operation": "create", "tableName": table,
            "columns": {"column": cols}, "options": {},
        }, onError="continueRegularOutput", executeOnce=True))
        clear = wf.add(node("Clear " + table, DT_TYPE, DT_VER, (x, 170), {
            "resource": "table", "operation": "clear", "dataTableId": dt_ref(table),
        }, onError="continueRegularOutput", executeOnce=True))
        emit = wf.add(code("Seed " + table, chr(10).join(lines), (x, 340)))
        ins = wf.add(dt_insert("Insert " + table, table, (x, 510)))
        wf.link(create, clear)
        wf.link(clear, emit)
        wf.link(emit, ins)
        if prev is None:
            wf.link(ack, create)
            wf.link(manual, create)
        else:
            wf.link(prev, create)
        prev = ins
        x += 250
    wf.nodes.append(sticky(chr(10).join([
        "## Provision & Seed",
        "`POST /munjiz/reset` (or run it manually) creates the six **n8n Data Tables**,",
        "clears them and loads the synthetic seed.",
        "",
        "No Google Sheet, no spreadsheet id, no OAuth - the datastore lives inside n8n.",
        "Idempotent, so this is also the reset button between rehearsals.",
    ]), (-1020, -360), width=640, height=220))
    return wf


# ---------------------------------------------------------------------------


REFLECT_FIND_JS = "const d = $json;\nconst now = Date.now();\n// Only look at the recent slice: reflection is cheap because it is bounded.\nconst recent = (d.transactions || []).filter(t => {\n  const ts = new Date(t.updated_at || t.ts).getTime();\n  return !isNaN(ts) && (now - ts) < 24 * 3600 * 1000;\n});\nconst audit = (d.audit || []).slice(0, 40);\nconst denials = audit.filter(a => String(a.result_summary || '').startsWith('DENIED'));\nconst batch = recent.map(t => ({ txn_id: t.txn_id, skill_id: t.skill_id,\n  status: t.status, type_ar: t.type_ar, employee_id: t.employee_id,\n  payload: t.payload_json, decision_note: t.decision_note }));\nreturn [{ json: { batch, batch_size: batch.length,\n  denial_count: denials.length,\n  denials: denials.map(a => ({ skill_id: a.skill_id, service: a.service })),\n  now: new Date().toISOString() } }];\n"
REFLECT_SYS_MSG = 'أنت «مراجع ما بعد الدور» في منظومة مُنجِز. تعمل بعد أن حصل الموظفون على إجاباتهم، ومهمتك الوحيدة تحسين ذاكرة المنظومة ومهاراتها. التزم حرفيًا بميثاق المراجعة المحمّل أدناه، وخصوصًا القائمة السلبية والفصل بين الذاكرة والمهارة. ابدأ دائمًا بـ read_memory قبل أي كتابة. مرور بلا تحديث = فرصة ضائعة، لكن لا تكتب ما تمنعه القائمة السلبية. أعد JSON فقط.'
REFLECT_SCHEMA = {'type': 'object', 'properties': {'memory_writes': {'type': 'array', 'items': {'type': 'object', 'properties': {'action': {'type': 'string'}, 'scope': {'type': 'string'}, 'content': {'type': 'string'}, 'why': {'type': 'string'}}, 'required': ['action', 'content', 'why']}}, 'patch_proposals': {'type': 'array', 'items': {'type': 'object', 'properties': {'skill_id': {'type': 'string'}, 'proposed_text': {'type': 'string'}, 'rationale': {'type': 'string'}}, 'required': ['skill_id', 'proposed_text', 'rationale']}}, 'skipped_reason': {'type': 'string', 'description': 'إن لم تُجرِ أي تحديث، اذكر لماذا صراحةً'}}, 'required': ['memory_writes', 'patch_proposals']}


def build_reflection():
    """The Hermes-style background review: a SECOND agent pass that runs after the
    employee already has their answer, whose only job is to improve the system's
    memory and skills. It is tool-restricted to the three learning services by the
    same governance gateway that constrains the service agent, and it can only ever
    FILE a skill proposal - never edit an approved skill."""
    wf = Wf("مُنجِز — 08 Reflection (learning pass)")
    sched = wf.add(node("Daily", "n8n-nodes-base.scheduleTrigger", 1.2, (-1200, -140),
                        {"rule": {"interval": [{"field": "hours", "hoursInterval": REFLECT_HOURS}]}}))
    manual = wf.add(node("Reflect Manually", "n8n-nodes-base.manualTrigger", 1, (-1200, 30), {}))
    hook = wf.add(node("Reflect Webhook", "n8n-nodes-base.webhook", 2, (-1200, 200),
                       {"httpMethod": "POST", "path": "munjiz/reflect",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    ack = wf.add(respond("Respond Reflect", '={{ { "ok": true, "started": true } }}', (-1000, 200)))
    wf.link(hook, ack)

    rd = wf.add(exec_wf("Read All (reflect)", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                        {"action": "read_all", "tab": ""}, (-960, 30)))
    for t in (sched, manual, ack):
        wf.link(t, rd)
    find = wf.add(code("Gather Batch", REFLECT_FIND_JS, (-740, 30)))
    wf.link(rd, find)
    gate = wf.add(if_node("Anything To Learn?", "={{ $json.batch_size }}", "number", "gt", 0,
                          (-520, 30)))
    wf.link(find, gate)
    idle = wf.add(node("Nothing New ✓", "n8n-nodes-base.noOp", 1, (-300, 200), {}))
    wf.link(gate, idle, output=1)

    charter = wf.add(dt_read("Load Reflection Charter", "Skills", (-300, -80)))
    wf.link(gate, charter, output=0)

    pick_charter = wf.add(code("Pick Charter", (
        "const rows = $input.all().map(i => i.json);\n"
        "const r = rows.find(x => x && x.skill_id === 'reflection') || {};\n"
        "return [{ json: { body_md: r.body_md || '' } }];\n"
    ), (-180, -80)))
    wf.link(charter, pick_charter)
    agent = wf.add(node("Reflection Agent", "@n8n/n8n-nodes-langchain.agent", 2.2, (-60, -80), {
        "promptType": "define",
        "text": "={{ 'ميثاق المراجعة:\\n' + ($json.body_md || '') + '\\n\\nدفعة المعاملات الأخيرة:\\n'"
                " + JSON.stringify($('Gather Batch').first().json.batch)"
                " + '\\n\\nحالات رفض الحوكمة:\\n'"
                " + JSON.stringify($('Gather Batch').first().json.denials) }}",
        "hasOutputParser": True,
        "options": {"systemMessage": REFLECT_SYS_MSG, "maxIterations": 12,
                    "returnIntermediateSteps": True},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=15000))
    wf.link(pick_charter, agent)
    lm = wf.add(node("Gemini Chat Model (reflect)", "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
                     1, (-180, 180), {"modelName": "models/" + MODEL_CHEAP,
                                      "options": {"temperature": 0.3}}, credentials=CRED_GEMINI))
    wf.link(lm, agent, ctype="ai_languageModel")
    parser = wf.add(node("Reflection Output", "@n8n/n8n-nodes-langchain.outputParserStructured",
                         1.2, (-20, 180),
                         {"schemaType": "manual",
                          "inputSchema": json.dumps(REFLECT_SCHEMA, ensure_ascii=False, indent=2)}))
    wf.link(parser, agent, ctype="ai_outputParser")
    tool = wf.add(node("call_service (learning)", "@n8n/n8n-nodes-langchain.toolWorkflow", 2.2,
                       (140, 180), {
        "name": "call_service",
        "description": ("بوابة الخدمات نفسها، لكن صلاحيتك محصورة في: read_memory (اقرأ الذاكرة أولًا)، "
                        "write_memory (add/replace/remove مع content)، propose_skill_patch "
                        "(skill_id + proposed_text + rationale). أي خدمة أخرى سترفضها الحوكمة."),
        "source": "database",
        "workflowId": wfref(GATEWAY_ID, "مُنجِز — 02 Service Gateway (sub)"),
        "workflowInputs": {"mappingMode": "defineBelow", "value": {
            "service": "={{ $fromAI('service', 'read_memory | write_memory | propose_skill_patch', 'string') }}",
            "payload": "={{ $fromAI('payload', 'JSON string payload for the service', 'string') }}",
            "skill_id": "reflection",
            "employee_id": "={{ $fromAI('employee_id', 'the employee this memory is about, or empty for org scope', 'string') }}",
            "session_id": "reflection",
        }, "matchingColumns": [], "schema": rm_schema(["service", "payload", "skill_id", "employee_id", "session_id"]),
            "attemptToConvertTypes": False, "convertFieldsToString": False}}))
    wf.link(tool, agent, ctype="ai_tool")

    log = wf.add(code("Log Reflection", (
        "const o = $json.output || {};\n"
        "const n = (o.memory_writes || []).length + (o.patch_proposals || []).length;\n"
        "return [{ json: { ts: new Date().toISOString(), session_id: 'reflection',\n"
        "  employee_id: '', skill_id: 'reflection', service: 'reflection_pass',\n"
        "  request_json: JSON.stringify({ batch: $('Gather Batch').first().json.batch_size }),\n"
        "  result_summary: n + ' تحديث: ' + ((o.memory_writes || []).map(m => m.why).join(' | ')\n"
        "    || o.skipped_reason || 'لا جديد') } }];\n"
    ), (180, -80)))
    wf.link(agent, log)
    logw = wf.add(dt_insert("Append Reflection Log", "AuditLog", (400, -80)))
    wf.link(log, logw)

    wf.nodes.append(sticky(chr(10).join([
        "## 08 Reflection — حلقة التعلّم",
        "A SECOND agent pass, after the employee already has their answer.",
        "",
        "Its charter (`skills/reflection.skill.md`) is itself a governed skill, so the",
        "reviewer cannot rewrite its own rules. The gateway restricts it to three",
        "services; memory is capped at 2200 chars per scope, and on overflow the write",
        "is refused with the full inventory attached so it must merge or delete.",
        "",
        "It may only FILE a skill proposal — approval is a human act (criterion ⑥).",
    ]), (-1220, -420), width=680, height=250))
    return wf


def build_patch_review():
    """Human approval of agent-proposed skill refinements."""
    wf = Wf("مُنجِز — 09 Patch Review")
    hook = wf.add(node("POST Patch", "n8n-nodes-base.webhook", 2, (-700, 0),
                       {"httpMethod": "POST", "path": "munjiz/patch",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    rd = wf.add(dt_read("Read SkillPatches (review)", "SkillPatches", (-480, 0)))
    wf.link(hook, rd)
    dec = wf.add(code("Apply Patch Decision", (
        "const b = $('POST Patch').first().json.body || {};\n"
        "const rows = $input.all().map(i => i.json).filter(r => r && r.patch_id);\n"
        "const t = rows.find(r => r.patch_id === b.patch_id);\n"
        "if (!t) return [{ json: { ok: false, error: 'PATCH_NOT_FOUND' } }];\n"
        "if (t.status !== 'pending') return [{ json: { ok: false, error: 'NOT_PENDING',\n"
        "  status: t.status } }];\n"
        "const d = String(b.decision || '').toLowerCase();\n"
        "if (d !== 'approve' && d !== 'reject')\n"
        "  return [{ json: { ok: false, error: 'INVALID_DECISION' } }];\n"
        "return [{ json: { ok: true, row: { ...t, status: d === 'approve' ? 'approved' : 'rejected',\n"
        "  reviewed_by: b.reviewer || 'owner', review_note: String(b.note || '').slice(0, 300),\n"
        "  updated_at: new Date().toISOString() } } }];\n"
    ), (-260, 0)))
    wf.link(rd, dec)
    ok = wf.add(if_node("Decision OK?", "={{ $json.ok }}", "boolean", "true", "true",
                        (-40, 0), single=True))
    wf.link(dec, ok)
    err = wf.add(respond("Respond Patch Error",
                         '={{ { "ok": false, "error": $json.error } }}', (180, 160)))
    wf.link(ok, err, output=1)
    emit = wf.add(code("Emit Patch Update", "return [{ json: $json.row }];", (180, -80)))
    wf.link(ok, emit, output=0)
    save = wf.add(dt_upsert("Save Patch Decision", "SkillPatches", "patch_id", (400, -80)))
    wf.link(emit, save)

    # An approval is the ONLY path that may change a skill. It appends the rule to
    # the body and bumps the patch version, so the procedure itself improves and the
    # version number is visible evidence of it.
    read_sk = wf.add(dt_read("Read Skills (apply)", "Skills", (620, -80)))
    wf.link(save, read_sk)
    apply_patch = wf.add(code("Apply To Skill", (
        "const dec = $('Apply Patch Decision').first().json.row;\n"
        "if (!dec || dec.status !== 'approved') return [];\n"
        "const rows = $input.all().map(i => i.json).filter(r => r && r.skill_id);\n"
        "const sk = rows.find(r => r.skill_id === dec.skill_id);\n"
        "if (!sk) return [];\n"
        "const parts = String(sk.version || '1.0.0').split('.');\n"
        "parts[2] = String((Number(parts[2]) || 0) + 1);  // patch-level bump\n"
        "const stamp = new Date().toISOString().slice(0, 10);\n"
        "const marker = '## تحسينات معتمدة (طبقة متعلَّمة)';\n"
        "let body = String(sk.body_md || '');\n"
        "if (body.indexOf(marker) === -1) body += '\\n\\n' + marker + '\\n';\n"
        "body += '\\n- ' + dec.proposed_text + '  \\n  _(' + dec.patch_id + ' — اعتمدها '\n"
        "  + (dec.reviewed_by || 'مالك الإجراء') + ' في ' + stamp + ')_\\n';\n"
        "return [{ json: { skill_id: sk.skill_id, version: parts.join('.'), status: sk.status,\n"
        "  title_ar: sk.title_ar, title_en: sk.title_en, keywords: sk.keywords,\n"
        "  profile_id: sk.profile_id, allowed_services: sk.allowed_services,\n"
        "  approval_chain: sk.approval_chain, auto_execute: sk.auto_execute,\n"
        "  sla_hours: sk.sla_hours, internal: sk.internal, body_md: body,\n"
        "  created_by: sk.created_by, updated_at: new Date().toISOString() } }];\n"
    ), (840, -80), alwaysOutputData=True))
    wf.link(read_sk, apply_patch)
    save_sk = wf.add(dt_upsert("Save Improved Skill", "Skills", "skill_id", (1060, -80)))
    wf.link(apply_patch, save_sk)
    resp = wf.add(respond("Respond Patch",
                          '={{ { "ok": true, "status": $(\'Apply Patch Decision\').first().json.row.status } }}',
                          (1280, -80)))
    wf.link(save_sk, resp)
    wf.nodes.append(sticky(chr(10).join([
        "## 09 Patch Review",
        "`POST /munjiz/patch {patch_id, decision, note, reviewer}`.",
        "An approved proposal becomes a **learned layer** appended to the governed",
        "base skill at load time — the agent still cannot touch the base file in git.",
    ]), (-720, -240), width=600, height=180))
    return wf


def merge(name, wf_id, parts, gap=1500):
    """Combine several built workflows onto one canvas.

    Safe because node names are globally unique across the parts: connections
    and $('Node') lookups are name-based, so nothing needs rewriting. Each part
    is pushed down the canvas by `gap` and labelled with a sticky note, so the
    merged workflow is still walkable during the judges' inspection.
    """
    out = Wf(name, wf_id)
    seen = {}
    y = 0
    for label, wf in parts:
        for n in wf.nodes:
            if n["type"] != "n8n-nodes-base.stickyNote":
                if n["name"] in seen:
                    raise SystemExit("merge collision: %r in %s and %s"
                                     % (n["name"], seen[n["name"]], label))
                seen[n["name"]] = label
            n["position"] = [n["position"][0], n["position"][1] + y]
            out.nodes.append(n)
        out.nodes.append(sticky("# " + label, (-2150, y - 80), width=300, height=130, color=3))
        for src, types in wf.conns.items():
            dst = out.conns.setdefault(src, {})
            for ct, outs in types.items():
                cur = dst.setdefault(ct, [])
                while len(cur) < len(outs):
                    cur.append([])
                for i, o in enumerate(outs):
                    cur[i].extend(o)
        y += gap
    return out


def fill_tool_input_schemas(doc):
    """toolWorkflow needs its resourceMapper `schema` populated or n8n passes NULL for
    every sub-workflow input (plain executeWorkflow tolerates an empty schema, which is
    why the Data IO calls worked while the agent's call_service silently sent nulls)."""
    for n in doc.get("nodes", []):
        if n.get("type") != "@n8n/n8n-nodes-langchain.toolWorkflow":
            continue
        wi = (n.get("parameters") or {}).get("workflowInputs") or {}
        vals = wi.get("value") or {}
        if vals and not wi.get("schema"):
            wi["schema"] = [{
                "id": k, "displayName": k, "required": False, "defaultMatch": False,
                "display": True, "canBeUsedToMatch": True, "type": "string",
            } for k in vals]
    return doc


def validate(doc):
    errs = []
    names = [n["name"] for n in doc["nodes"]]
    if len(names) != len(set(names)):
        errs.append("duplicate node names: %s" % sorted({x for x in names if names.count(x) > 1}))
    for n in doc["nodes"]:
        for k in ("id", "name", "type", "typeVersion", "position", "parameters"):
            if k not in n:
                errs.append("node %s missing %s" % (n.get("name", "?"), k))
    ns = set(names)
    for src, types in doc["connections"].items():
        if src not in ns:
            errs.append("source not a node: %s" % src)
        for ct, outs in types.items():
            for out in outs:
                for t in out:
                    if t["node"] not in ns:
                        errs.append("target not a node: %s -> %s" % (src, t["node"]))
    return errs


def emit(outdir, builds):
    os.makedirs(outdir, exist_ok=True)
    bad = False
    for fname, wf in builds:
        wf.wf_id = wf.wf_id or WF_IDS.get(fname)
        doc = fill_tool_input_schemas(wf.dump())
        errs = validate(doc)
        if errs:
            bad = True
            print("FAIL", fname)
            for e in errs:
                print("  -", e)
        with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print("  %-26s nodes=%-3d conns=%d" % (fname, len(doc["nodes"]), len(doc["connections"])))
    return bad


def main():
    print("workflow-split/ (8 files, one per concern)")
    bad = emit(OUT_SPLIT, [
        ("00-data-io.json", build_data_io()),
        ("01-chat-agent.json", build_agent()),
        ("02-service-gateway.json", build_gateway()),
        ("03-approvals.json", build_approvals()),
        ("04-sla-chaser.json", build_chaser()),
        ("05-dashboard-api.json", build_dash()),
        ("06-error-handler.json", build_error()),
        ("07-demo-reset.json", build_seed()),
        ("08-reflection.json", build_reflection()),
        ("09-patch-review.json", build_patch_review()),
    ])

    # Default set: the five trigger workflows merged onto one canvas.
    # 00 Data IO and 02 Service Gateway MUST stay separate (they are invoked via
    # executeWorkflow / toolWorkflow, which can only target another workflow),
    # and the error handler stays separate so it can be assigned as one.
    main_wf = merge(MAIN_NAME, WF_MAIN_ID, [
        ("01 Chat Agent", build_agent()),
        ("03 Approvals", build_approvals()),
        ("04 SLA Chaser", build_chaser()),
        ("05 Dashboard API", build_dash()),
        ("07 Provision & Seed", build_seed()),
        ("08 Reflection", build_reflection()),
        ("09 Patch Review", build_patch_review()),
    ])
    print("workflow/ (4 files, merged - the default import set)")
    bad = emit(OUT, [
        ("00-data-io.json", build_data_io()),
        ("01-main.json", main_wf),
        ("02-service-gateway.json", build_gateway()),
        ("03-error-handler.json", build_error()),
    ]) or bad

    if bad:
        raise SystemExit(1)
    print("all workflows valid")


if __name__ == "__main__":
    main()
