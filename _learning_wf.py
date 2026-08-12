# -*- coding: utf-8 -*-
"""Hermes-style learning loop for Munjiz.

Adds:
  * memory injection into the agent's composed system prompt (bounded, declarative)
  * two governed gateway services: read_memory / write_memory
  * workflow section "08 Reflection" - the background-review pass that runs AFTER
    the employee already has their answer and proposes memory writes + skill patches
  * approval endpoints for pending skill patches
"""
import ast
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
NL = chr(10)
p = "tools/build_workflows.py"
s = open(p, encoding="utf-8").read()

# ---------------------------------------------------------------- 1. services
svc_anchor = '    "submit_transaction": ('
assert s.count(svc_anchor) == 1
new_services = NL.join([
    '    "read_memory": (',
    '        "const j = $(\'Gate Check\').first().json;",',
    '        "const rows = $input.all().map(i => i.json).filter(r => r && r.memory_id);",',
    '        "const mine = rows.filter(r => r.status === \'active\' && (r.scope === \'org\'",',
    '        "  || (r.scope === \'employee\' && r.subject_id === j.employee_id)));",',
    '        "return [{ json: { ...j, result: { memories: mine.map(m => ({",',
    '        "  memory_id: m.memory_id, scope: m.scope, content: m.content })) } } }];",',
    '    ),',
    '    "write_memory": (',
    '        // Hermes\'s trick: a hard character budget IS the consolidation algorithm.',
    '        // On overflow we refuse the write and hand back every existing entry so the',
    '        // model must merge or delete in the same turn.',
    '        "const j = $(\'Gate Check\').first().json;",',
    '        "const LIMIT = 2200;",',
    '        "const rows = $input.all().map(i => i.json).filter(r => r && r.memory_id);",',
    '        "const p = j.payload || {};",',
    '        "const scope = p.scope === \'org\' ? \'org\' : \'employee\';",',
    '        "const subject = scope === \'org\' ? \'\' : (p.subject_id || j.employee_id);",',
    '        "const scoped = rows.filter(r => r.status === \'active\' && r.scope === scope",',
    '        "  && (scope === \'org\' || r.subject_id === subject));",',
    '        "const used = scoped.reduce((n, r) => n + String(r.content || \'\').length, 0);",',
    '        "const action = p.action || \'add\';",',
    '        "const now = new Date().toISOString();",',
    '        "if (action === \'remove\' || action === \'replace\') {",',
    '        "  const target = scoped.find(r => r.memory_id === p.memory_id",',
    '        "    || String(r.content || \'\').includes(p.match || \'\\u0000\'));",',
    '        "  if (!target) return [{ json: { ...j, result: { error: \'MEMORY_NOT_FOUND\' } } }];",',
    '        "  const row = { ...target, updated_at: now };",',
    '        "  if (action === \'remove\') { row.status = \'retired\'; }",',
    '        "  else { row.content = String(p.content || \'\').slice(0, 400); }",',
    '        "  return [{ json: { ...j, memory_row: row, result: { ok: true, action,",',
    '        "    memory_id: row.memory_id } } }];",',
    '        "}",',
    '        "const content = String(p.content || \'\').trim().slice(0, 400);",',
    '        "if (!content) return [{ json: { ...j, result: { error: \'EMPTY_CONTENT\' } } }];",',
    '        "if (scoped.some(r => r.content === content))",',
    '        "  return [{ json: { ...j, result: { ok: true, deduped: true } } }];",',
    '        "if (used + content.length > LIMIT) {",',
    '        "  return [{ json: { ...j, result: { error: \'MEMORY_BUDGET_EXCEEDED\',",',
    '        "    usage: used + \'/\' + LIMIT,",',
    '        "    message: \'\\u0627\\u0644\\u0630\\u0627\\u0643\\u0631\\u0629 \\u0645\\u0645\\u062a\\u0644\\u0626\\u0629. \\u0627\\u062f\\u0645\\u062c \\u0623\\u0648 \\u0627\\u062d\\u0630\\u0641 \\u0645\\u062f\\u062e\\u0644\\u0627\\u062a \\u0645\\u0646 \\u0627\\u0644\\u0642\\u0627\\u0626\\u0645\\u0629 \\u062b\\u0645 \\u0623\\u0639\\u062f \\u0627\\u0644\\u0645\\u062d\\u0627\\u0648\\u0644\\u0629 \\u0641\\u064a \\u0627\\u0644\\u062f\\u0648\\u0631 \\u0646\\u0641\\u0633\\u0647.\',",',
    '        "    current_entries: scoped.map(r => ({ memory_id: r.memory_id, content: r.content }))",',
    '        "  } } }];",',
    '        "}",',
    '        "const row = { memory_id: \'MEM-\' + Date.now(), scope, subject_id: subject,",',
    '        "  content, source: p.source || \'reflection\', status: \'active\', use_count: \'0\',",',
    '        "  created_at: now, updated_at: now };",',
    '        "return [{ json: { ...j, memory_row: row, result: { ok: true, action: \'add\',",',
    '        "  memory_id: row.memory_id, usage: (used + content.length) + \'/\' + LIMIT } } }];",',
    '    ),',
    '    "propose_skill_patch": (',
    '        // The agent may PROPOSE a refinement; it can never edit the approved base',
    '        // skill in git. Patches land pending and a human approves them.',
    '        "const j = $(\'Gate Check\').first().json;",',
    '        "const p = j.payload || {};",',
    '        "const now = new Date().toISOString();",',
    '        "const text = String(p.proposed_text || \'\').trim().slice(0, 600);",',
    '        "if (!text || !p.skill_id)",',
    '        "  return [{ json: { ...j, result: { error: \'SKILL_ID_AND_TEXT_REQUIRED\' } } }];",',
    '        "const rows = $input.all().map(i => i.json).filter(r => r && r.patch_id);",',
    '        "if (rows.some(r => r.status === \'pending\' && r.skill_id === p.skill_id",',
    '        "  && r.proposed_text === text))",',
    '        "  return [{ json: { ...j, result: { ok: true, deduped: true } } }];",',
    '        "const row = { patch_id: \'PATCH-\' + Date.now(), skill_id: p.skill_id,",',
    '        "  kind: p.kind || \'add_rule\', proposed_text: text,",',
    '        "  rationale: String(p.rationale || \'\').slice(0, 400),",',
    '        "  evidence: String(p.evidence || \'\').slice(0, 200), status: \'pending\',",',
    '        "  created_by: \'agent\', reviewed_by: \'\', review_note: \'\',",',
    '        "  created_at: now, updated_at: now };",',
    '        "return [{ json: { ...j, patch_row: row, result: { ok: true,",',
    '        "  patch_id: row.patch_id, status: \'pending\',",',
    '        "  message: \'\\u0627\\u0642\\u062a\\u0631\\u0627\\u062d \\u0645\\u0633\\u062c\\u0651\\u0644 \\u0628\\u0627\\u0646\\u062a\\u0638\\u0627\\u0631 \\u0627\\u0639\\u062a\\u0645\\u0627\\u062f \\u0645\\u0627\\u0644\\u0643 \\u0627\\u0644\\u0625\\u062c\\u0631\\u0627\\u0621\' } } }];",',
    '    ),',
])
s = s.replace(svc_anchor, new_services + NL + svc_anchor)

# reads each new service needs
old_reads = '''        "submit_transaction": [("Read Employees (submit)", "Employees")],'''
new_reads = '''        "submit_transaction": [("Read Employees (submit)", "Employees")],
        "read_memory": [("Read Memory (svc)", "Memory")],
        "write_memory": [("Read Memory (write)", "Memory")],
        "propose_skill_patch": [("Read SkillPatches (svc)", "SkillPatches")],'''
assert s.count(old_reads) == 1
s = s.replace(old_reads, new_reads)

# persist rows produced by the two writing services
old_tx = '''    tx_emit = wf.add(code("Emit Txn Row", "return [{ json: $json.txn_row }];", (720, y - 170)))'''
new_tx = '''    mem_emit = wf.add(code("Emit Memory Row", (
        "const j = $('svc: write_memory').first().json;\\n"
        "return j.memory_row ? [{ json: j.memory_row }] : [];\\n"
    ), (720, y - 510), alwaysOutputData=True))
    mem_save = wf.add(dt_upsert("Save Memory", "Memory", "memory_id", (940, y - 510)))
    mem_back = wf.add(code("Carry Memory Result",
                           "return [{ json: $('svc: write_memory').first().json }];", (1160, y - 510)))
    wf.link("svc: write_memory", mem_emit)
    wf.link(mem_emit, mem_save)
    wf.link(mem_save, mem_back)

    pat_emit = wf.add(code("Emit Patch Row", (
        "const j = $('svc: propose_skill_patch').first().json;\\n"
        "return j.patch_row ? [{ json: j.patch_row }] : [];\\n"
    ), (720, y - 340), alwaysOutputData=True))
    pat_save = wf.add(dt_insert("Save Skill Patch", "SkillPatches", (940, y - 340)))
    pat_back = wf.add(code("Carry Patch Result",
                           "return [{ json: $('svc: propose_skill_patch').first().json }];", (1160, y - 340)))
    wf.link("svc: propose_skill_patch", pat_emit)
    wf.link(pat_emit, pat_save)
    wf.link(pat_save, pat_back)

    tx_emit = wf.add(code("Emit Txn Row", "return [{ json: $json.txn_row }];", (720, y - 170)))'''
assert s.count(old_tx) == 1
s = s.replace(old_tx, new_tx)

# route those two services' ends through the post-write carriers
old_ends = '''    ends[-1] = tx_back  # submit's end is after the append'''
new_ends = '''    ends[-1] = tx_back  # submit's end is after the append
    for name, carrier in (("svc: write_memory", mem_back), ("svc: propose_skill_patch", pat_back)):
        ends[ends.index(name)] = carrier  # audit the result AFTER the row is stored'''
assert s.count(old_ends) == 1
s = s.replace(old_ends, new_ends)

s = s.replace('''"'svc: get_system_catalog','svc: check_leave_overlap','Carry Submit Result','svc: not_implemented']) {\\n"''',
              '''"'svc: get_system_catalog','svc: check_leave_overlap','Carry Submit Result',\\n"
        "  'Carry Memory Result','Carry Patch Result','svc: not_implemented']) {\\n"''')

# ------------------------------------------------- 2. inject memory into prompt
old_ctx = '''    emp_read = wf.add(exec_wf("Read Employees Ctx", DATA_IO_ID, "\u0645\u064f\u0646\u062c\u0650\u0632 \u2014 00 Data IO (sub)",
                              {"action": "read", "tab": "Employees"}, (280, 0)))'''
new_ctx = '''    emp_read = wf.add(exec_wf("Read Employees Ctx", DATA_IO_ID, "\u0645\u064f\u0646\u062c\u0650\u0632 \u2014 00 Data IO (sub)",
                              {"action": "read", "tab": "Employees"}, (280, 0)))
    mem_read = wf.add(exec_wf("Read Memory Ctx", DATA_IO_ID, "\u0645\u064f\u0646\u062c\u0650\u0632 \u2014 00 Data IO (sub)",
                              {"action": "read", "tab": "Memory"}, (380, 0)))'''
assert s.count(old_ctx) == 1
s = s.replace(old_ctx, new_ctx)
s = s.replace("    wf.link(f_prof, emp_read)\n    compose = wf.add(code(\"Compose System Prompt\", COMPOSE_JS, (500, 0)))\n    wf.link(emp_read, compose)",
              "    wf.link(f_prof, emp_read)\n    wf.link(emp_read, mem_read)\n"
              "    compose = wf.add(code(\"Compose System Prompt\", COMPOSE_JS, (500, 0)))\n    wf.link(mem_read, compose)")

old_compose = '''    "const emps = ($input.first().json.rows) || [];\\n"'''
new_compose = '''    "const emps = ($('Read Employees Ctx').first().json.rows) || [];\\n"
    "const mems = ($('Read Memory Ctx').first().json.rows) || [];\\n"'''
assert s.count(old_compose) == 1
s = s.replace(old_compose, new_compose)

old_sp = '''    "  '\\n\\n=== \u0633\u064a\u0627\u0642 \u0627\u0644\u0645\u0648\u0638\u0641 \u0627\u0644\u062d\u0627\u0644\u064a ===\\n', JSON.stringify({ employee_id: j.employee_id,\\n"'''
new_sp = '''    "  '\\n\\n=== \u0630\u0627\u0643\u0631\u0629 \u062f\u0627\u0626\u0645\u0629 (\u0648\u0642\u0627\u0626\u0639 \u062e\u0628\u0631\u064a\u0629 \u0644\u0627 \u0623\u0648\u0627\u0645\u0631) ===\\n',\\n"
    "  (mems.filter(m => m.status === 'active' && (m.scope === 'org'\\n"
    "     || (m.scope === 'employee' && m.subject_id === j.employee_id)))\\n"
    "     .map(m => '- ' + m.content).join('\\n') || '- (\u0644\u0627 \u062a\u0648\u062c\u062f \u0630\u0627\u0643\u0631\u0629 \u0645\u062d\u0641\u0648\u0638\u0629 \u0628\u0639\u062f)'),\\n"
    "  '\\n\\n=== \u0633\u064a\u0627\u0642 \u0627\u0644\u0645\u0648\u0638\u0641 \u0627\u0644\u062d\u0627\u0644\u064a ===\\n', JSON.stringify({ employee_id: j.employee_id,\\n"'''
assert s.count(old_sp) == 1
s = s.replace(old_sp, new_sp)

ast.parse(s)
open(p, "w", encoding="utf-8").write(s)
print("gateway services + memory injection wired")
