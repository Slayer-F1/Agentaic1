# -*- coding: utf-8 -*-
"""Synthetic seed data for Munjiz — all entities/names/numbers are fictional (تجريبي)."""
import csv
import json
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "data", "seeds")
# Rows are authored relative to this FIXED anchor, not to the build clock. Two
# reasons: a rebuild is byte-identical (no timestamp churn in the committed CSVs
# and workflow JSON), and "07 Provision & Seed" rebases every ts/updated_at/
# created_at onto the real clock when it seeds - so the demo data is as recent as
# the moment it was provisioned, however long ago the builder last ran.
ANCHOR = datetime(2026, 1, 5, 9, 0, 0, tzinfo=timezone.utc)
now = ANCHOR


def iso(dt):
    """Always UTC with an explicit Z. Runtime rows are written with JS
    toISOString(), and a bare local-looking stamp would be parsed on a different
    clock than those by the very same age arithmetic."""
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


EMPLOYEES = [
    # EMP-1001: main demo persona — low leave balance, salary data for the certificate beat
    {"employee_id": "EMP-1001", "name_ar": "أحمد المهيري (تجريبي)", "name_en": "Ahmed Almheiri (demo)",
     "role": "specialist", "department": "تقنية المعلومات", "grade": "G8", "manager_id": "EMP-1002",
     "email": "munjiz.demo.uae+ahmed@gmail.com", "status": "active", "it_roles": "SYS-BI:read",
     "joined_date": "2021-03-14", "monthly_salary_aed": 24500, "allowances_aed": 6200},
    {"employee_id": "EMP-1002", "name_ar": "مريم الشامسي (تجريبي)", "name_en": "Mariam Alshamsi (demo)",
     "role": "manager", "department": "تقنية المعلومات", "grade": "G11", "manager_id": "EMP-1007",
     "email": "munjiz.demo.uae+mariam@gmail.com", "status": "active", "it_roles": "SYS-BI:write;SYS-CRM:read",
     "joined_date": "2016-09-01", "monthly_salary_aed": 41000, "allowances_aed": 9800},
    {"employee_id": "EMP-1003", "name_ar": "سالم النقبي (تجريبي)", "name_en": "Salem Alnaqbi (demo)",
     "role": "specialist", "department": "تقنية المعلومات", "grade": "G7", "manager_id": "EMP-1002",
     "email": "munjiz.demo.uae+salem@gmail.com", "status": "active", "it_roles": "SYS-BI:read",
     "joined_date": "2022-11-20", "monthly_salary_aed": 21000, "allowances_aed": 5400},
    {"employee_id": "EMP-1004", "name_ar": "راشد الكتبي (تجريبي)", "name_en": "Rashed Alketbi (demo)",
     "role": "specialist", "department": "الاتصال المؤسسي", "grade": "G8", "manager_id": "EMP-1005",
     "email": "munjiz.demo.uae+rashed@gmail.com", "status": "active", "it_roles": "",
     "joined_date": "2020-01-05", "monthly_salary_aed": 23000, "allowances_aed": 5800},
    {"employee_id": "EMP-1005", "name_ar": "نورة الظاهري (تجريبي)", "name_en": "Noura Aldhaheri (demo)",
     "role": "manager", "department": "الاتصال المؤسسي", "grade": "G11", "manager_id": "EMP-1007",
     "email": "munjiz.demo.uae+noura@gmail.com", "status": "active", "it_roles": "SYS-CRM:write",
     "joined_date": "2015-06-15", "monthly_salary_aed": 39500, "allowances_aed": 9200},
    {"employee_id": "EMP-1006", "name_ar": "خالد الهاملي (تجريبي)", "name_en": "Khaled Alhameli (demo)",
     "role": "finance", "department": "المالية", "grade": "G9", "manager_id": "EMP-1007",
     "email": "munjiz.demo.uae+khaled@gmail.com", "status": "active", "it_roles": "SYS-ERP:write",
     "joined_date": "2018-02-10", "monthly_salary_aed": 28500, "allowances_aed": 6900},
    {"employee_id": "EMP-1007", "name_ar": "عبدالله السويدي (تجريبي)", "name_en": "Abdulla Alsuwaidi (demo)",
     "role": "it_security", "department": "أمن المعلومات", "grade": "G12", "manager_id": "",
     "email": "munjiz.demo.uae+abdulla@gmail.com", "status": "active", "it_roles": "SYS-ERP:admin;SYS-CRM:admin",
     "joined_date": "2013-04-22", "monthly_salary_aed": 47000, "allowances_aed": 11000},
]

BALANCES = [
    {"employee_id": "EMP-1001", "annual_total": 30, "annual_used": 22, "sick_total": 15, "sick_used": 2},
    {"employee_id": "EMP-1002", "annual_total": 30, "annual_used": 10, "sick_total": 15, "sick_used": 0},
    {"employee_id": "EMP-1003", "annual_total": 30, "annual_used": 4, "sick_total": 15, "sick_used": 1},
    {"employee_id": "EMP-1004", "annual_total": 30, "annual_used": 12, "sick_total": 15, "sick_used": 3},
    {"employee_id": "EMP-1005", "annual_total": 30, "annual_used": 8, "sick_total": 15, "sick_used": 0},
    {"employee_id": "EMP-1006", "annual_total": 30, "annual_used": 15, "sick_total": 15, "sick_used": 4},
    {"employee_id": "EMP-1007", "annual_total": 30, "annual_used": 6, "sick_total": 15, "sick_used": 0},
]

POLICY = [
    {"category": "transport", "monthly_cap_aed": 400, "receipt_required_above": 100,
     "notes": "مواصلات المهام الرسمية داخل الدولة"},
    {"category": "hospitality", "monthly_cap_aed": 1000, "receipt_required_above": 100,
     "notes": "ضيافة رسمية معتمدة مسبقًا"},
    {"category": "training", "monthly_cap_aed": 2000, "receipt_required_above": 100,
     "notes": "رسوم برامج ومؤتمرات معتمدة"},
    {"category": "communication", "monthly_cap_aed": 300, "receipt_required_above": 100,
     "notes": "بدل اتصالات للمهام الميدانية"},
    {"category": "other", "monthly_cap_aed": 500, "receipt_required_above": 100,
     "notes": "بموجب وصف تفصيلي إلزامي"},
]

SYSTEMS = [
    {"system_id": "SYS-BI", "name_ar": "منصة التقارير والمؤشرات", "name_en": "BI & Reports Platform",
     "sensitivity": "normal", "allowed_roles": "specialist;manager;finance"},
    {"system_id": "SYS-CRM", "name_ar": "نظام علاقات المتعاملين", "name_en": "Customer Relations System",
     "sensitivity": "sensitive", "allowed_roles": "specialist;manager;customer_service"},
    {"system_id": "SYS-ERP", "name_ar": "نظام الموارد المؤسسية", "name_en": "Enterprise Resource System",
     "sensitivity": "critical", "allowed_roles": "finance;manager"},
    {"system_id": "SYS-HRMS", "name_ar": "نظام الموارد البشرية", "name_en": "HR Management System",
     "sensitivity": "sensitive", "allowed_roles": "hr;manager"},
]

nxt = now + timedelta(days=7)
TRANSACTIONS = [
    # سالم's approved leave next week — powers the overlap-warning beat for أحمد
    # Submitted and approved inside the last day, so the reflection pass (which only
    # looks at the trailing 24h) always has at least one served request to learn from.
    {"txn_id": "TXN-SEED-OVERLAP", "ts": iso(now - timedelta(hours=20)), "employee_id": "EMP-1003",
     "employee_name": "سالم النقبي (تجريبي)", "skill_id": "leave-request", "type_ar": "طلب إجازة",
     "payload_json": json.dumps({"leave_type": "annual", "start_date": nxt.date().isoformat(),
                                 "end_date": (nxt + timedelta(days=4)).date().isoformat(),
                                 "working_days": 3, "reason": "إجازة عائلية"}, ensure_ascii=False),
     "status": "executed", "approval_chain": "manager", "chain_pos": 1, "current_approver": "",
     "decision_note": "اعتمدت", "output_ref": "", "sla_hours": 48, "updated_at": iso(now - timedelta(hours=6))},
    # راشد's stale claim — the SLA-chaser anchor (reset re-arms it too)
    {"txn_id": "TXN-SEED-CHASE", "ts": iso(now - timedelta(hours=30)), "employee_id": "EMP-1004",
     "employee_name": "راشد الكتبي (تجريبي)", "skill_id": "expense-claim", "type_ar": "مطالبة نفقات / بدلات",
     "payload_json": json.dumps({"category": "training", "amount_aed": 850,
                                 "expense_date": (now - timedelta(days=6)).date().isoformat(),
                                 "description": "رسوم ورشة تدريبية معتمدة", "receipt_ref": "RCPT-7741",
                                 "approver_report": "الموظف: راشد الكتبي (تجريبي) — EMP-1004 — الاتصال المؤسسي — G8 | الطلب: استرداد 850 درهمًا رسوم ورشة تدريبية معتمدة بتاريخ قريب | التحقق: الفئة training سقفها الشهري 2000 درهم والمصروف السابق 0 — المبلغ ضمن السقف؛ رقم الإيصال RCPT-7741 مرفق كما تشترط السياسة فوق 100 درهم؛ التاريخ ضمن مهلة 60 يومًا | التوصية: اعتماد — الطلب مستوفٍ لجميع شروط السياسة."},
                                ensure_ascii=False),
     "status": "awaiting_manager", "approval_chain": "manager;finance", "chain_pos": 0,
     "current_approver": "manager", "decision_note": "", "output_ref": "", "sla_hours": 24,
     "updated_at": iso(now - timedelta(hours=30))},
    # a historical executed certificate — populates KPIs
    {"txn_id": "TXN-SEED-CERT", "ts": iso(now - timedelta(days=9)), "employee_id": "EMP-1006",
     "employee_name": "خالد الهاملي (تجريبي)", "skill_id": "salary-certificate",
     "type_ar": "شهادة راتب / لمن يهمه الأمر",
     "payload_json": json.dumps({"certificate_type": "employment", "addressed_to": "لمن يهمه الأمر",
                                 "language": "ar",
                                 "certificate_text": "تشهد الهيئة الاتحادية للخدمات المشتركة (تجريبي) بأن السيد خالد الهاملي يعمل لدينا بوظيفة محاسب عمليات مالية بإدارة المالية منذ 2018-02-10 وما زال على رأس عمله حتى تاريخه. وقد أُصدرت هذه الشهادة بناءً على طلبه دون أدنى مسؤولية على الهيئة تجاه الغير."}, ensure_ascii=False),
     "status": "executed", "approval_chain": "", "chain_pos": 0, "current_approver": "",
     "decision_note": "", "output_ref": "CERT-118204", "sla_hours": 1,
     "updated_at": iso(now - timedelta(days=9))},
]

# These two rows ARE the service calls that created TXN-SEED-OVERLAP, so they must
# track its ts (now - 20h) — an audit trail that predates its own transaction is the
# one thing the الحوكمة view must never show.
AUDIT = [
    {"ts": iso(now - timedelta(hours=20, seconds=30)), "session_id": "S-seed-1", "employee_id": "EMP-1003",
     "skill_id": "leave-request", "service": "get_leave_balance", "request_json": "{}",
     "result_summary": "OK {\"annual_remaining\":26,...}"},
    {"ts": iso(now - timedelta(hours=20)), "session_id": "S-seed-1", "employee_id": "EMP-1003",
     "skill_id": "leave-request", "service": "submit_transaction",
     "request_json": "{\"leave_type\":\"annual\"}", "result_summary": "OK TXN-SEED-OVERLAP awaiting_manager"},
]

# ---------------------------------------------------------------------------
# Learning stores (Hermes-style). Memory holds DECLARATIVE facts — "who the
# employee is / what the standing situation is" — never procedures; procedures
# belong in skills. SkillPatches holds agent-proposed refinements to a skill,
# which stay PENDING until a human approves them: the agent may never edit the
# approved base procedure in git, only propose a layer on top of it.
# ---------------------------------------------------------------------------

MEMORY = [
    {"memory_id": "MEM-0001", "scope": "org", "subject_id": "",
     "content": "تُغلق إدارة المالية حساباتها الشهرية في آخر ثلاثة أيام عمل من كل شهر، وتتأخر اعتمادات المطالبات في تلك الفترة.",
     "source": "seed", "status": "active", "use_count": "0",
     "created_at": iso(now - timedelta(days=20)), "updated_at": iso(now - timedelta(days=20))},
    {"memory_id": "MEM-0002", "scope": "employee", "subject_id": "EMP-1001",
     "content": "يفضّل أحمد المهيري الردود المختصرة والمباشرة، ويطلب دائمًا تأكيد التواريخ بالتقويم الميلادي.",
     "source": "seed", "status": "active", "use_count": "0",
     "created_at": iso(now - timedelta(days=6)), "updated_at": iso(now - timedelta(days=6))},
    {"memory_id": "MEM-0003", "scope": "employee", "subject_id": "EMP-1004",
     "content": "راشد الكتبي يقدّم مطالبات نفقات تدريبية بشكل متكرر، وغالبًا ما ينسى إرفاق رقم الإيصال.",
     "source": "seed", "status": "active", "use_count": "0",
     "created_at": iso(now - timedelta(days=3)), "updated_at": iso(now - timedelta(days=3))},
]

SKILL_PATCHES = [
    {"patch_id": "PATCH-0001", "skill_id": "expense-claim", "kind": "add_rule",
     "proposed_text": "عند اختيار الفئة training: ذكّر الموظف برقم الإيصال قبل عرض بطاقة المعاينة، فقد لوحظ تكرار نسيانه.",
     "rationale": "ثلاث مطالبات تدريبية متتالية رُدّت لغياب رقم الإيصال.",
     "evidence": "TXN-SEED-CHASE", "status": "pending", "created_by": "agent",
     "reviewed_by": "", "review_note": "",
     "created_at": iso(now - timedelta(hours=5)), "updated_at": iso(now - timedelta(hours=5))},
]

# ---------------------------------------------------------------------------
# The runtime skill library. Seeded from the authored markdown in skills/ and
# profiles/, but from here on it lives inside n8n: an approved patch rewrites
# body_md and bumps version, so procedures genuinely evolve. `created_by`
# carries the Hermes provenance rule - 'human' rows are the approved base and
# only a human approval may change them; the agent can never write here directly.
# ---------------------------------------------------------------------------

def _read(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return ""
    return open(full, encoding="utf-8").read()


def _load_registry():
    reg = json.load(open(os.path.join(ROOT, "registry", "skills-index.json"), encoding="utf-8"))
    skills, profiles, seen = [], [], set()
    for sk in reg["skills"]:
        skills.append({
            "skill_id": sk["id"],
            "version": sk["version"],
            "status": sk["status"],
            "title_ar": sk["title_ar"],
            "title_en": sk["title_en"],
            "keywords": ";".join(sk.get("keywords", [])),
            "profile_id": os.path.basename(sk["profile_path"]).split(".")[0],
            "allowed_services": ";".join(sk.get("allowed_services", [])),
            "approval_chain": ";".join(sk.get("approval_chain", [])),
            "auto_execute": "true" if sk.get("auto_execute") else "false",
            "sla_hours": str(sk.get("sla_hours", 48)),
            "internal": "true" if sk.get("internal") else "false",
            "body_md": _read(sk["skill_path"]),
            "created_by": "human",
            "updated_at": iso(now),
        })
        pid = os.path.basename(sk["profile_path"]).split(".")[0]
        if pid not in seen:
            seen.add(pid)
            profiles.append({"profile_id": pid, "body_md": _read(sk["profile_path"])})
    return skills, profiles


SKILLS, PROFILES = _load_registry()

TABS = {
    "Employees": (["employee_id", "name_ar", "name_en", "role", "department", "grade", "manager_id",
                   "email", "status", "it_roles", "joined_date", "monthly_salary_aed", "allowances_aed"], EMPLOYEES),
    "LeaveBalances": (["employee_id", "annual_total", "annual_used", "sick_total", "sick_used"], BALANCES),
    "ExpensePolicy": (["category", "monthly_cap_aed", "receipt_required_above", "notes"], POLICY),
    "SystemCatalog": (["system_id", "name_ar", "name_en", "sensitivity", "allowed_roles"], SYSTEMS),
    "Transactions": (["txn_id", "ts", "employee_id", "employee_name", "skill_id", "type_ar", "payload_json",
                      "status", "approval_chain", "chain_pos", "current_approver", "decision_note",
                      "output_ref", "sla_hours", "updated_at"], TRANSACTIONS),
    "AuditLog": (["ts", "session_id", "employee_id", "skill_id", "service", "request_json",
                  "result_summary"], AUDIT),
    "Memory": (["memory_id", "scope", "subject_id", "content", "source", "status",
                "use_count", "created_at", "updated_at"], MEMORY),
    "SkillPatches": (["patch_id", "skill_id", "kind", "proposed_text", "rationale", "evidence",
                      "status", "created_by", "reviewed_by", "review_note",
                      "created_at", "updated_at"], SKILL_PATCHES),
    "Skills": (["skill_id", "version", "status", "title_ar", "title_en", "keywords",
                "profile_id", "allowed_services", "approval_chain", "auto_execute",
                "sla_hours", "internal", "body_md", "created_by", "updated_at"], SKILLS),
    "Profiles": (["profile_id", "body_md"], PROFILES),
}


def _pin_xlsx(path):
    """Rewrite an .xlsx so two builds of the same rows are byte-identical: every zip
    entry stamped at ANCHOR, and dcterms:modified pinned too (openpyxl rewrites that
    one with the wall clock during save(), ignoring wb.properties)."""
    import re
    import zipfile
    stamp = ANCHOR.timetuple()[:6]
    anchor_z = ANCHOR.strftime("%Y-%m-%dT%H:%M:%SZ").encode()
    tmp = path + ".tmp"
    try:
        with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename == "docProps/core.xml":
                    data = re.sub(rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)",
                                  rb"\g<1>" + anchor_z + rb"\g<2>", data)
                info = zipfile.ZipInfo(item.filename, date_time=stamp)
                info.compress_type = item.compress_type
                info.external_attr = item.external_attr
                out.writestr(info, data)
        # os.replace, not shutil.move: on Windows shutil.move falls back to a non-atomic
        # copy when the destination exists, so a failure mid-copy would truncate the real
        # file while the cleanup below removed the only intact copy.
        os.replace(tmp, path)
    finally:
        # On success the replace consumed tmp; on any failure this clears the stray file
        # (and both archives are already closed, so nothing holds a lock on Windows).
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    os.makedirs(SEEDS, exist_ok=True)
    for tab, (headers, rows) in TABS.items():
        with open(os.path.join(SEEDS, tab + ".csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print("wrote seeds/%s.csv (%d rows)" % (tab, len(rows)))
    try:
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
        for tab, (headers, rows) in TABS.items():
            ws = wb.create_sheet(title=tab)
            ws.sheet_view.rightToLeft = True
            ws.append(headers)
            for r in rows:
                ws.append([r.get(h, "") for h in headers])
        # openpyxl stamps docProps and every zip entry with the wall clock, which would
        # leave this the one build output that churns on every run. `created` is the only
        # one that survives save(); _pin_xlsx handles dcterms:modified and the entry times.
        wb.properties.created = ANCHOR.replace(tzinfo=None)
        xlsx = os.path.join(SEEDS, "munjiz-registry-seed.xlsx")
        wb.save(xlsx)
        _pin_xlsx(xlsx)
        print("wrote seeds/munjiz-registry-seed.xlsx")
    except ImportError:
        print("openpyxl missing — CSVs only")


if __name__ == "__main__":
    main()
