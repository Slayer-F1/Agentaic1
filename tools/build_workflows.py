# -*- coding: utf-8 -*-
"""Builds the importable n8n workflow JSONs for Munjiz (مُنجِز) — skill-governed transactions agent.

Run:  python tools/build_workflows.py     → workflow/*.json

User-replaced placeholders (find & replace before import):
  REPLACE_WITH_SPREADSHEET_ID   Google Sheet id of the seeded "Munjiz Registry"
The GitHub raw base defaults to the real Agentaic1 repo (public) and can be edited in one node.
"""
import json
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "workflow")
OUT_SPLIT = os.path.join(ROOT, "workflow-split")
SHEET = {"__rl": True, "value": "REPLACE_WITH_SPREADSHEET_ID", "mode": "id"}
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
RAW_BASE = "https://raw.githubusercontent.com/Slayer-F1/Agentaic1/main/"
DEMO_INBOX = "munjiz.demo.uae@gmail.com"

CRED_GEMINI = {"googlePalmApi": {"id": "GEMINI_CRED_ID", "name": "Google Gemini (AI Studio)"}}
CRED_SHEETS = {"googleSheetsOAuth2Api": {"id": "SHEETS_CRED_ID", "name": "Google Sheets (demo)"}}
CRED_GMAIL = {"gmailOAuth2": {"id": "GMAIL_CRED_ID", "name": "Gmail (demo)"}}


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


def sheets_read(name, tab, pos, dyn=None):
    sn = {"__rl": True, "value": dyn or tab, "mode": "name"}
    return node(name, "n8n-nodes-base.googleSheets", 4.5, pos,
                {"operation": "read", "documentId": SHEET, "sheetName": sn, "options": {}},
                credentials=CRED_SHEETS, alwaysOutputData=True,
                retryOnFail=True, maxTries=3, waitBetweenTries=4000)


def sheets_append(name, tab, pos):
    return node(name, "n8n-nodes-base.googleSheets", 4.5, pos,
                {"operation": "append", "documentId": SHEET,
                 "sheetName": {"__rl": True, "value": tab, "mode": "name"},
                 "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [],
                             "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True},
                 "options": {}},
                credentials=CRED_SHEETS, retryOnFail=True, maxTries=3, waitBetweenTries=4000)


def sheets_upsert(name, tab, match, pos):
    return node(name, "n8n-nodes-base.googleSheets", 4.5, pos,
                {"operation": "appendOrUpdate", "documentId": SHEET,
                 "sheetName": {"__rl": True, "value": tab, "mode": "name"},
                 "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [match],
                             "schema": [], "attemptToConvertTypes": False, "convertFieldsToString": True},
                 "options": {}},
                credentials=CRED_SHEETS, retryOnFail=True, maxTries=3, waitBetweenTries=4000)


def code(name, js, pos, **extra):
    return node(name, "n8n-nodes-base.code", 2, pos, {"jsCode": js}, **extra)


def gemini(name, pos, field="geminiBody"):
    return node(name, "n8n-nodes-base.httpRequest", 4.2, pos,
                {"method": "POST", "url": GEMINI_URL,
                 "authentication": "predefinedCredentialType", "nodeCredentialType": "googlePalmApi",
                 "sendBody": True, "specifyBody": "json",
                 "jsonBody": "={{ JSON.stringify($json." + field + ") }}",
                 "options": {"timeout": 90000}},
                credentials=CRED_GEMINI, retryOnFail=True, maxTries=3, waitBetweenTries=6000)


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

    rt = wf.add(sheets_read("Read Tab", "Employees", (-200, -140),
                            dyn="={{ $('Data Input').first().json.tab }}"))
    wrap = wf.add(code("Wrap Rows", (
        "const rows = $input.all().map(i => i.json).filter(r => r && Object.keys(r).length > 0);\n"
        "return [{ json: { tab: $('Data Input').first().json.tab, count: rows.length, rows } }];\n"
    ), (60, -140)))
    wf.link(sw, rt, output=0)
    wf.link(rt, wrap)

    tabs = ["Employees", "LeaveBalances", "ExpensePolicy", "SystemCatalog", "Transactions", "AuditLog"]
    prev = None
    x = -200
    for t in tabs:
        n = wf.add(sheets_read("Read " + t, t, (x, 140)))
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
        "  policy: grab('Read ExpensePolicy'), systems: grab('Read SystemCatalog'),\n"
        "  transactions: grab('Read Transactions'), audit: grab('Read AuditLog'),\n"
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
    "let index = null;\n"
    "try { index = JSON.parse($json.data ?? $json.body ?? $json.gemini_text ?? ''); } catch (e) {}\n"
    "if (!index) { try { index = typeof $json === 'object' && $json.skills ? $json : null; } catch (e) {} }\n"
    "const skills = (index && index.skills) || [];\n"
    "const skill = skills.find(s => s.id === inp.skill_id && s.status === 'approved');\n"
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
    fetch = wf.add(http_raw("Fetch Skills Index", RAW_BASE + "registry/skills-index.json", (-980, 0)))
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
    }
    for i, svc in enumerate(services):
        x = -60
        prev = None
        for rname, tab in reads_map[svc]:
            n = wf.add(sheets_read(rname, tab, (x, y)))
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
    tx_emit = wf.add(code("Emit Txn Row", "return [{ json: $json.txn_row }];", (720, y - 170)))
    tx_append = wf.add(sheets_append("Append Transaction", "Transactions", (940, y - 170)))
    tx_back = wf.add(code("Carry Submit Result",
                          "return [{ json: $('svc: submit_transaction').first().json }];", (1160, y - 170)))
    wf.link("svc: submit_transaction", tx_emit)
    wf.link(tx_emit, tx_append)
    wf.link(tx_append, tx_back)
    ends[-1] = tx_back  # submit's end is after the append

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
    audit_append = wf.add(sheets_append("Append AuditLog", "AuditLog", (1620, 60)))
    wf.link(audit_row, audit_append)
    ret = wf.add(code("Return Result", (
        "const src = $('Build Audit Row').first().json;\n"
        "// find the full item that produced the audit row\n"
        "let full = null;\n"
        "for (const n of ['Denied Result','svc: get_employee_profile','svc: get_leave_balance',\n"
        "  'svc: get_salary_record','svc: get_expense_policy','svc: get_it_roles',\n"
        "  'svc: get_system_catalog','svc: check_leave_overlap','Carry Submit Result','svc: not_implemented']) {\n"
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

AGENT_OUT_SCHEMA = {
    "type": "object",
    "properties": {
        "reply_ar": {"type": "string"},
        "state": {"type": "string", "enum": ["collecting", "preview", "submitted", "rejected", "escalated", "info"]},
        "transaction_preview": {"type": ["object", "null"],
                                "properties": {"fields": {"type": "object"},
                                               "working_days": {"type": ["number", "null"]},
                                               "amount_aed": {"type": ["number", "null"]},
                                               "approval_chain": {"type": "array", "items": {"type": "string"}},
                                               "warnings": {"type": "array", "items": {"type": "string"}}}},
        "txn_id": {"type": ["string", "null"]},
        "missing_fields": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["reply_ar", "state"],
}

ROUTER_JS = (
    "const b = $('Chat Webhook').first().json.body || {};\n"
    "let index = {};\n"
    "try { index = JSON.parse($('Fetch Skills Index').first().json.data); } catch (e) {\n"
    "  try { index = $('Fetch Skills Index').first().json; } catch (e2) {}\n"
    "}\n"
    "const skills = (index.skills || []).filter(s => s.status === 'approved');\n"
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
    "const skillMd = $('Fetch Skill MD').first().json.data || '';\n"
    "const profileMd = $('Fetch Profile MD').first().json.data || '';\n"
    "const emps = ($input.first().json.rows) || [];\n"
    "const me = emps.find(r => r.employee_id === j.employee_id) || {};\n"
    "const charter = " + json.dumps(CHARTER, ensure_ascii=False) + ";\n"
    "const system_prompt = [charter,\n"
    "  '\\n\\n=== ملف الخبرة المعتمد ===\\n', profileMd,\n"
    "  '\\n\\n=== المهارة المعتمدة (v' + (j.skill_meta.version || '') + ') ===\\n', skillMd,\n"
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
    fetch_idx = wf.add(http_raw("Fetch Skills Index", RAW_BASE + "registry/skills-index.json", (-1480, 0)))
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

    f_skill = wf.add(http_raw("Fetch Skill MD",
                              "={{ '" + RAW_BASE + "' + $json.skill_meta.skill_path }}", (-160, 0)))
    wf.link(matched, f_skill, output=0)
    f_prof = wf.add(http_raw("Fetch Profile MD",
                             "={{ '" + RAW_BASE + "' + $('Pick Skill').first().json.skill_meta.profile_path }}", (60, 0)))
    wf.link(f_skill, f_prof)
    emp_read = wf.add(exec_wf("Read Employees Ctx", DATA_IO_ID, "مُنجِز — 00 Data IO (sub)",
                              {"action": "read", "tab": "Employees"}, (280, 0)))
    wf.link(f_prof, emp_read)
    compose = wf.add(code("Compose System Prompt", COMPOSE_JS, (500, 0)))
    wf.link(emp_read, compose)

    agent = wf.add(node("Munjiz Agent", "@n8n/n8n-nodes-langchain.agent", 2.2, (760, 0),
                        {"promptType": "define",
                         "text": "={{ $json.message }}",
                         "hasOutputParser": True,
                         "options": {"systemMessage": "={{ $json.system_prompt }}",
                                     "maxIterations": 10, "returnIntermediateSteps": True}},
                        retryOnFail=True, maxTries=2, waitBetweenTries=8000))
    lm = wf.add(node("Gemini Chat Model", "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", 1, (620, 260),
                     {"modelName": "models/gemini-2.5-flash", "options": {"temperature": 0.2}},
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
    r1 = wf.add(sheets_read("Read Transactions (decide)", "Transactions", (-880, 0)))
    r2 = wf.add(sheets_read("Read Employees (decide)", "Employees", (-660, 0)))
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
    upd = wf.add(sheets_upsert("Update Transaction", "Transactions", "txn_id", (220, -80)))
    wf.link(upd_emit, upd)

    r3 = wf.add(sheets_read("Read LeaveBalances (side)", "LeaveBalances", (440, -80)))
    r4 = wf.add(sheets_read("Read Employees (side)", "Employees", (660, -80)))
    wf.link(upd, r3)
    wf.link(r3, r4)
    side = wf.add(code("Apply Side Effect", SIDE_JS.replace("const j = $json;",
                                                            "const j = $('Decide').first().json;"), (880, -80),
                       alwaysOutputData=True))
    wf.link(r4, side)
    has_side = wf.add(if_node("Leave Side?", "={{ $json.annual_used !== undefined || $json.sick_used !== undefined }}",
                              "boolean", "true", "true", (1100, -80), single=True))
    wf.link(side, has_side)
    up_bal = wf.add(sheets_upsert("Update LeaveBalances", "LeaveBalances", "employee_id", (1320, -180)))
    wf.link(has_side, up_bal, output=0)
    has_it = wf.add(if_node("IT Side?", "={{ $json.it_roles !== undefined }}", "boolean", "true", "true",
                            (1320, 0), single=True))
    wf.link(has_side, has_it, output=1)
    up_emp = wf.add(sheets_upsert("Update Employee Roles", "Employees", "employee_id", (1540, -60)))
    wf.link(has_it, up_emp, output=0)
    conv = wf.add(node("Converge", "n8n-nodes-base.noOp", 1, (1540, 120), {}))
    wf.link(has_it, conv, output=1)
    wf.link(up_bal, conv)
    wf.link(up_emp, conv)

    mail = wf.add(node("Notify Employee", "n8n-nodes-base.gmail", 2.1, (1760, 120),
                       {"sendTo": "={{ $('Decide').first().json.owner_email }}",
                        "subject": "=مُنجِز: تحديث معاملتك {{ $('Decide').first().json.txn.txn_id }}",
                        "message": "={{ 'حالة معاملتك (' + $('Decide').first().json.txn.type_ar + ') أصبحت: ' + $('Decide').first().json.update.status + ($('Decide').first().json.update.decision_note ? ' — ملاحظة: ' + $('Decide').first().json.update.decision_note : '') }}",
                        "options": {}}, credentials=CRED_GMAIL, onError="continueRegularOutput"))
    wf.link(conv, mail)
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
    sched = wf.add(node("Every 5 Minutes", "n8n-nodes-base.scheduleTrigger", 1.2, (-1100, -120),
                        {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}}))
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
                        retryOnFail=True, maxTries=2, waitBetweenTries=8000))
    wf.link(any_, agent, output=0)
    lm = wf.add(node("Gemini Chat Model (chaser)", "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", 1, (-300, 180),
                     {"modelName": "models/gemini-2.5-flash", "options": {"temperature": 0.2}},
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
    logw = wf.add(sheets_append("Append AuditLog (chaser)", "AuditLog", (520, -40)))
    wf.link(audit_rows, logw)
    carry = wf.add(code("Carry Decisions", "return $('Flatten').all();", (740, -40)))
    wf.link(logw, carry)
    act = wf.add(switch_rules("Chaser Switch", "={{ $json.action }}", ["remind_approver", "escalate"], (960, -40)))
    wf.link(carry, act)
    remind = wf.add(node("Remind Approver", "n8n-nodes-base.gmail", 2.1, (540, -140),
                         {"sendTo": "={{ $json.approver_email || '" + DEMO_INBOX + "' }}",
                          "subject": "=⏰ مُنجِز: معاملة بانتظار اعتمادك — {{ $json.txn_id }}",
                          "message": "={{ $json.type_ar + ' للموظف ' + $json.employee + ' منذ ' + $json.age_hours + ' ساعة. ' + $json.justification_ar }}",
                          "options": {}}, credentials=CRED_GMAIL, onError="continueRegularOutput"))
    wf.link(act, remind, output=0)
    esc = wf.add(node("Escalate", "n8n-nodes-base.gmail", 2.1, (540, 60),
                      {"sendTo": DEMO_INBOX,
                       "subject": "=🔺 مُنجِز: معاملة تجاوزت SLA — {{ $json.txn_id }}",
                       "message": "={{ $json.type_ar + ' للموظف ' + $json.employee + ' متأخرة ' + $json.age_hours + ' ساعة (sla ' + $json.sla_hours + '). ' + $json.justification_ar }}",
                       "options": {}}, credentials=CRED_GMAIL, onError="continueRegularOutput"))
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
    "let index = {};\n"
    "try { index = JSON.parse($('Fetch Skills Index (dash)').first().json.data); } catch (e) {}\n"
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
    idx = wf.add(http_raw("Fetch Skills Index (dash)", RAW_BASE + "registry/skills-index.json", (-480, 0)))
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
        "return [{ json: { wf: (j.workflow || {}).name || '?', node: (j.execution || {}).lastNodeExecuted || '?',\n"
        "  msg: ((j.execution || {}).error || {}).message || '?', at: new Date().toISOString() } }];\n"
    ), (-280, 0)))
    mail = wf.add(node("Notify", "n8n-nodes-base.gmail", 2.1, (-60, 0),
                       {"sendTo": DEMO_INBOX, "subject": "=⚙️ مُنجِز — خطأ تشغيلي: {{ $json.wf }}",
                        "message": "={{ 'Node: ' + $json.node + ' — ' + $json.msg + ' @ ' + $json.at }}",
                        "options": {}}, credentials=CRED_GMAIL, onError="continueRegularOutput"))
    done = wf.add(node("Logged ✓", "n8n-nodes-base.noOp", 1, (160, 0), {}))
    wf.link(trig, ext)
    wf.link(ext, mail)
    wf.link(mail, done)
    wf.nodes.append(sticky("## Error Handler (criterion ⑥)\nSet as error workflow for 01/03/04/05.",
                           (-520, -180), width=440, height=120))
    return wf


def build_reset():
    wf = Wf("مُنجِز — 07 Demo Reset")
    hook = wf.add(node("POST Reset", "n8n-nodes-base.webhook", 2, (-640, 0),
                       {"httpMethod": "POST", "path": "munjiz/reset",
                        "responseMode": "responseNode", "options": {}}, webhook=True))
    comp = wf.add(code("Compute Anchors", (
        "// Re-arm demo anchors: canonical leave balances for the two demo employees\n"
        "// and one stale pending transaction for the chaser beat.\n"
        "const now = new Date();\n"
        "const stale = new Date(now.getTime() - 30 * 3600 * 1000).toISOString();\n"
        "return [{ json: {\n"
        "  bal1: { employee_id: 'EMP-1001', annual_total: 30, annual_used: 22, sick_total: 15, sick_used: 2 },\n"
        "  bal2: { employee_id: 'EMP-1003', annual_total: 30, annual_used: 4, sick_total: 15, sick_used: 0 },\n"
        "  staleTxn: { txn_id: 'TXN-SEED-CHASE', ts: stale, employee_id: 'EMP-1004',\n"
        "    employee_name: 'راشد الكتبي (تجريبي)', skill_id: 'expense-claim', type_ar: 'مطالبة نفقات / بدلات',\n"
        "    payload_json: JSON.stringify({ category: 'training', amount_aed: 850, expense_date: stale.slice(0, 10),\n"
        "      description: 'رسوم ورشة تدريبية معتمدة', receipt_ref: 'RCPT-7741' }),\n"
        "    status: 'awaiting_manager', approval_chain: 'manager;finance', chain_pos: 0,\n"
        "    current_approver: 'manager', decision_note: '', output_ref: '', sla_hours: 24, updated_at: stale },\n"
        "} }];\n"
    ), (-420, 0)))
    wf.link(hook, comp)
    b1 = wf.add(code("Emit Bal 1", "return [{ json: $json.bal1 }];", (-200, -120)))
    u1 = wf.add(sheets_upsert("Reset Balance 1", "LeaveBalances", "employee_id", (20, -120)))
    b2 = wf.add(code("Emit Bal 2", "return [{ json: $('Compute Anchors').first().json.bal2 }];", (240, -120)))
    u2 = wf.add(sheets_upsert("Reset Balance 2", "LeaveBalances", "employee_id", (460, -120)))
    b3 = wf.add(code("Emit Stale Txn", "return [{ json: $('Compute Anchors').first().json.staleTxn }];", (680, -120)))
    u3 = wf.add(sheets_upsert("Seed Stale Txn", "Transactions", "txn_id", (900, -120)))
    resp = wf.add(respond("Respond Reset", '={{ { "ok": true } }}', (1120, 0)))
    wf.link(comp, b1)
    wf.link(b1, u1)
    wf.link(u1, b2)
    wf.link(b2, u2)
    wf.link(u2, b3)
    wf.link(b3, u3)
    wf.link(u3, resp)
    wf.nodes.append(sticky("## Demo Reset\n`POST /munjiz/reset` — canonical balances + a 30-hour-old "
                           "pending claim so the SLA chaser has something to rescue on stage.",
                           (-660, -260), width=560, height=150))
    return wf


# ---------------------------------------------------------------------------

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
        doc = wf.dump()
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
        ("07-demo-reset.json", build_reset()),
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
        ("07 Demo Reset", build_reset()),
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
