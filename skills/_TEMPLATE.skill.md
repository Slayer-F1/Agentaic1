---
id: <kebab-case-id>
version: 0.1.0
status: draft            # draft skills are NOT loadable — flip to approved via a reviewed commit
title_ar: <الاسم العربي>
title_en: <English name>
owner: <owning unit>
profile: <hr-officer | finance-officer | it-officer | general>
allowed_services: []     # the ONLY services the gateway will execute for this skill
approval_chain: []       # [] = auto_execute allowed; e.g. [manager, finance]
auto_execute: false
sla_hours: 48
---

# مهارة: <العنوان>

## الغرض
جملة أو جملتان: ماذا تنجز هذه المهارة ولمن.

## الحقول المطلوبة
| الحقل | القيم | ملاحظات |
|---|---|---|

## قواعد الأهلية والسياسة (طبّقها حرفيًا وبالترتيب)
1. …

## خطوات الإجراء
1. get_employee_profile أولًا دائمًا.
2. اجمع الحقول الناقصة (سؤال مركّز واحد في كل رسالة).
3. …
4. اعرض بطاقة معاينة كاملة.
5. بعد تأكيد الموظف فقط: submit_transaction.

## التصعيد والاستثناءات
- …

## ما لا يجوز (خطوط حمراء)
- …

> **حوكمة:** أضِف المهارة إلى `registry/skills-index.json` (نفس الحقول أعلاه + keywords) — لا تصبح متاحة للوكيل إلا بذلك، وبحالة approved.
