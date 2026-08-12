# -*- coding: utf-8 -*-
"""Synthetic seed data for Munjiz — all entities/names/numbers are fictional (تجريبي)."""
import csv
import json
import os
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "data", "seeds")
now = datetime.now()


def iso(dt):
    return dt.isoformat(timespec="seconds")


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
    {"txn_id": "TXN-SEED-OVERLAP", "ts": iso(now - timedelta(days=2)), "employee_id": "EMP-1003",
     "employee_name": "سالم النقبي (تجريبي)", "skill_id": "leave-request", "type_ar": "طلب إجازة",
     "payload_json": json.dumps({"leave_type": "annual", "start_date": nxt.date().isoformat(),
                                 "end_date": (nxt + timedelta(days=4)).date().isoformat(),
                                 "working_days": 3, "reason": "إجازة عائلية"}, ensure_ascii=False),
     "status": "executed", "approval_chain": "manager", "chain_pos": 1, "current_approver": "",
     "decision_note": "اعتمدت", "output_ref": "", "sla_hours": 48, "updated_at": iso(now - timedelta(days=1))},
    # راشد's stale claim — the SLA-chaser anchor (reset re-arms it too)
    {"txn_id": "TXN-SEED-CHASE", "ts": iso(now - timedelta(hours=30)), "employee_id": "EMP-1004",
     "employee_name": "راشد الكتبي (تجريبي)", "skill_id": "expense-claim", "type_ar": "مطالبة نفقات / بدلات",
     "payload_json": json.dumps({"category": "training", "amount_aed": 850,
                                 "expense_date": (now - timedelta(days=6)).date().isoformat(),
                                 "description": "رسوم ورشة تدريبية معتمدة", "receipt_ref": "RCPT-7741"},
                                ensure_ascii=False),
     "status": "awaiting_manager", "approval_chain": "manager;finance", "chain_pos": 0,
     "current_approver": "manager", "decision_note": "", "output_ref": "", "sla_hours": 24,
     "updated_at": iso(now - timedelta(hours=30))},
    # a historical executed certificate — populates KPIs
    {"txn_id": "TXN-SEED-CERT", "ts": iso(now - timedelta(days=9)), "employee_id": "EMP-1006",
     "employee_name": "خالد الهاملي (تجريبي)", "skill_id": "salary-certificate",
     "type_ar": "شهادة راتب / لمن يهمه الأمر",
     "payload_json": json.dumps({"certificate_type": "employment", "addressed_to": "لمن يهمه الأمر",
                                 "language": "ar"}, ensure_ascii=False),
     "status": "executed", "approval_chain": "", "chain_pos": 0, "current_approver": "",
     "decision_note": "", "output_ref": "CERT-118204", "sla_hours": 1,
     "updated_at": iso(now - timedelta(days=9))},
]

AUDIT = [
    {"ts": iso(now - timedelta(days=2)), "session_id": "S-seed-1", "employee_id": "EMP-1003",
     "skill_id": "leave-request", "service": "get_leave_balance", "request_json": "{}",
     "result_summary": "OK {\"annual_remaining\":26,...}"},
    {"ts": iso(now - timedelta(days=2)), "session_id": "S-seed-1", "employee_id": "EMP-1003",
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
}


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
        wb.save(os.path.join(SEEDS, "munjiz-registry-seed.xlsx"))
        print("wrote seeds/munjiz-registry-seed.xlsx")
    except ImportError:
        print("openpyxl missing — CSVs only")


if __name__ == "__main__":
    main()
