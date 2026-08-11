---
id: it-access-request
version: 1.0.0
status: approved
title_ar: طلب صلاحية نظام
title_en: IT System Access Request
owner: IT Security (أمن المعلومات)
profile: it-officer
allowed_services: [get_employee_profile, get_it_roles, get_system_catalog, submit_transaction]
approval_chain: [manager, it_security]
auto_execute: false
sla_hours: 24
---

# مهارة: طلب صلاحية نظام

## الغرض
طلب منح أو ترقية صلاحية على نظام مؤسسي، مع فرض مبدأ **الحد الأدنى من الصلاحيات** وفحص الأهلية الوظيفية قبل وصول الطلب لسلسلة الاعتماد الأمنية.

## الحقول المطلوبة
| الحقل | القيم | ملاحظات |
|---|---|---|
| system_id | من get_system_catalog | إن ذكر الموظف اسمًا تجاريًا فطابقه مع الدليل وأكّد |
| access_level | read \| write \| admin | اشرح الفرق إذا تردد الموظف |
| business_justification | نص | إلزامي دائمًا؛ اربطه بمهمة وظيفية محددة |
| duration | permanent \| temporary(end_date) | المؤقتة تُفضَّل ويذكر ذلك |

## قواعد الأهلية والسياسة
1. من get_system_catalog: للنظام قائمة أدوار مخوّلة (allowed_roles) ودرجة حساسية (normal / sensitive / critical).
2. دور الموظف (من get_employee_profile) خارج allowed_roles ⇒ **ارفض** مع ذكر الأدوار المخوّلة نصًا؛ لا استثناءات محادثةً.
3. access_level = admin ⇒ مبرر تفصيلي + duration مؤقتة إلزامية + إضافة ciso إلى سلسلة الاعتماد.
4. النظام critical ⇒ حتى صلاحية القراءة تمر عبر it_security، وأدرج تحذير الحساسية في المعاينة.
5. الموظف يملك الصلاحية نفسها أو أعلى (من get_it_roles) ⇒ أخبره ولا تنشئ طلبًا مكررًا.
6. طبّق دائمًا الحد الأدنى: إن كفت read لمبرر الموظف فاقترحها بدل write واذكر السبب.

## خطوات الإجراء
1. get_employee_profile ثم get_it_roles للصلاحيات الحالية.
2. get_system_catalog لمطابقة النظام وقراءة حساسيته وأدواره.
3. اجمع الحقول وطبّق القواعد أعلاه بالترتيب.
4. اعرض **بطاقة معاينة**: النظام، المستوى، المدة، المبرر، سلسلة الاعتماد الكاملة، وتحذير الحساسية إن وجد.
5. بعد تأكيد الموظف: submit_transaction.

## التصعيد والاستثناءات
- طلب «مستعجل جدًا» لتجاوز السلسلة ⇒ ارفض التجاوز واشرح أن السلسلة قصيرة (sla 24 ساعة).
- نظام غير موجود في الدليل ⇒ needs_attention لفريق التقنية؛ لا تخترع أنظمة.

## ما لا يجوز
- لا منح فوري لأي صلاحية، لا admin دائمة، لا طلب نيابة عن موظف آخر، ولا قبول مبرر عام («أحتاجه لعملي») دون مهمة محددة.
