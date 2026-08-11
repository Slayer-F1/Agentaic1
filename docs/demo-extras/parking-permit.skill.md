---
id: parking-permit
version: 1.0.0
status: approved
title_ar: تصريح مواقف
title_en: Parking Permit
owner: Facilities (المرافق)
profile: general
allowed_services: [get_employee_profile, submit_transaction]
approval_chain: [manager]
auto_execute: false
sla_hours: 24
---

# مهارة: تصريح مواقف

> **هذه مهارة «الإضافة الحية» في العرض:** تُنسخ إلى `skills/` ويُضاف بندها إلى `registry/skills-index.json` أمام لجنة التحكيم — فيتقن الوكيل إجراءً جديدًا بالكامل خلال ثوانٍ، دون تعديل أي تدفق في n8n.
> بند السجل الجاهز للّصق موجود في نهاية هذا الملف.

## الغرض
طلب تصريح موقف سيارة شهري في مواقف المبنى للموظفين.

## الحقول المطلوبة
| الحقل | القيم | ملاحظات |
|---|---|---|
| plate_number | نص | رقم اللوحة والإمارة |
| vehicle_type | sedan \| suv \| motorcycle | |
| start_month | YYYY-MM | لا يُقبل شهر ماضٍ |

## قواعد الأهلية والسياسة
1. تصريح واحد فعّال لكل موظف؛ وجود تصريح فعّال ⇒ ارفض واذكر تاريخ انتهائه.
2. الدراجات النارية في المنطقة B حصرًا — اذكر ذلك في المعاينة.

## خطوات الإجراء
1. get_employee_profile.
2. اجمع الحقول، طبّق القواعد، اعرض بطاقة المعاينة (المنطقة، الشهر، اللوحة، المعتمِد).
3. بعد التأكيد: submit_transaction.

## التصعيد والاستثناءات
- طلب منطقة محددة ⇒ خارج نطاق المهارة؛ سجّل رغبة الموظف في الملاحظة فقط.

## ما لا يجوز
- لا حجز مواقف الزوار أو مواقف أصحاب الهمم.

---

بند `skills-index.json` الجاهز:

```json
{
  "id": "parking-permit",
  "version": "1.0.0",
  "status": "approved",
  "title_ar": "تصريح مواقف",
  "title_en": "Parking Permit",
  "keywords": ["موقف", "مواقف", "تصريح", "سيارة", "parking", "permit", "لوحة"],
  "skill_path": "skills/parking-permit.skill.md",
  "profile_path": "profiles/general.profile.md",
  "allowed_services": ["get_employee_profile", "submit_transaction"],
  "approval_chain": ["manager"],
  "auto_execute": false,
  "sla_hours": 24
}
```
