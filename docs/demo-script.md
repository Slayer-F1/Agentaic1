# سيناريو العرض الحي (٨ دقائق) — Live Demo Script
## مُنجِز (Munjiz)

**Stage:** projector on the portal (AR) · tab 2: n8n canvas + Executions · tab 3: GitHub repo (skills folder) · `POST /munjiz/reset` fired 30 min before · personas: أحمد (موظف)، مريم (مديرة).

### [0:00–0:40] الافتتاحية

> «كم إجراءً اعتياديًا في جهتكم؟ خمسون؟ مئة؟ أتمتة كلٍّ منها اليوم تعني بناء نظام لكل إجراء — فلا يُؤتمت إلا أكبرها. مُنجِز وكيل واحد يتقنها كلها، لأن كل إجراء عنده ملفُ مهارةٍ محوكم.»

Show the governance view: 4 skill cards, versions, allowlists — «هذه ليست وثائق؛ هذه هي الصلاحيات المنفَّذة.»

### [0:40–2:30] المعاملة الأولى — إجازة أحمد

As أحمد, type: «أريد إجازة الأسبوع القادم». Narrate what judges see live:
- the router picks **leave-request v1.2.0** and the agent introduces itself with the HR persona;
- it fetched his balance itself (8 days left), asks one focused question;
- give dates → it **warns about سالم's approved overlapping leave** (it read the team's registry — memory across runs);
- the preview card: fields, working days (weekend skipped — invite judges to count), approval chain;
- click تأكيد → submitted. Switch persona to مريم → الاعتمادات → approve → back as أحمد: balance dropped.

> «لم يفتح نموذجًا، لم يعرف قاعدة واحدة مسبقًا — والطلب وصل مديره سليمًا من أول مرة.»

### [2:30–3:40] الشهادة الفورية + برهان الحوكمة

As أحمد: «أحتاج شهادة راتب للبنك» → preview → confirm → **CERT number + certificate renders** (auto-execute, chain = فوري).
Then the governance money-shot — in the same certificate chat ask: «بالمناسبة كم رصيد إجازتي؟»

> The gateway REFUSES: this skill's allowlist has no get_leave_balance. Open الحوكمة → the red DENIED row in the audit log.
> «الوكيل نفسه لا يستطيع تجاوز مهارته. الحوكمة كود يُنفَّذ، لا سياسة تُنسى.»

### [3:40–5:00] الإضافة الحية — the killer beat

> «أهم سؤال في الأتمتة: كم يكلف الإجراء التالي؟ عندنا: ملف واحد.»

In the GitHub tab: copy `parking-permit.skill.md` into `skills/`, paste its block into `skills-index.json`, commit & push **on camera**. Back in the portal: «أريد تصريح موقف» → the agent handles the brand-new procedure — collects plate/month, previews, submits.

> «أضفنا إجراءً حكوميًا كاملًا في تسعين ثانية، ولم نلمس n8n إطلاقًا. هكذا تصل الأتمتة إلى كل الإجراءات لا كبيرها فقط.»

### [5:00–5:50] حارس الإنجاز

الإعدادات → «تشغيل حارس الإنجاز» («يعمل كل ٥ دقائق وحده — أطلقه الآن كي لا ننتظر»). The 30-hour-old claim of راشد triggers: the model chooses remind/escalate with a written justification → email + audit rows appear.

> «لا معاملة تعلق في درج أحد. الوكيل يطارد الاعتمادات بنفسه.»

### [5:50–7:00] فحص اللجنة — داخل n8n

Open the leave execution: the think-tool plan, the sequence of call_service choices (the model decided which services and when), the deterministic working-day cross-check node, the dynamic system prompt assembled from GitHub (show the fetched SKILL.md content in the execution data), credentials manager (key lives only there).

> «كتاب المهارة يأتي من git بمراجعة وإصدار؛ القرار يأتي من النموذج؛ والبوابة تسجل كل شيء.»

### [7:00–8:00] الخاتمة

> «إجراء اعتيادي: من نموذج يُرفض بعد أيام إلى محادثة دقيقتين لا تقبل المخالفة أصلًا. كلفة أتمتة الإجراء الجديد: ملف markdown واحد. وكل استدعاء بيانات — حتى المرفوض — مسجّل بمسوّغه. مُنجِز ليس روبوت محادثة؛ إنه موظف خدمات يتقن كل إجراء لأن كل إجراء كتب له كتابه.»

Invite a judge: pick any persona and try a request — or ask the certificate agent for something outside its skill and watch governance say no.

## Contingencies

| Risk | Response |
|---|---|
| GitHub raw cache lag on the live-add (~1 min) | Push the skill BEFORE walking on stage as backup; if the live push lags, narrate the governance story over the portal's skill registry until it lands. |
| Gemini 429 | Retries with backoff — narrate as self-correction. Fresh key for demo day. |
| Router mismatch on an odd phrasing | Rephrase naturally («أريد إجازة سنوية») — or click the service card in the sidebar (it pre-fills the request). |
| Network death | n8n + portal are local; hotspot backup; a cached successful execution open in tab 4. |
| Overrun | The chaser beat is skippable (mention it over the audit view); rehearse to 7:30. |
