# سيناريو العرض الحي (٨ دقائق) — Live Demo Script
## مُنجِز (Munjiz)

**Stage:** projector on the portal (AR) · tab 2: n8n canvas of `مُنجِز — Main` + Executions · personas ready in the switcher: أحمد (موظف)، نورة (مديرة راشد)، خالد (مالية) · `POST /munjiz/reset` fired 30 min before · quota hygiene: fresh Gemini key, no rehearsals on the demo key that day.

### [0:00–0:40] الافتتاحية

> «كم إجراءً اعتياديًا في جهتكم؟ خمسون؟ مئة؟ أتمتة كلٍّ منها اليوم تعني بناء نظام لكل إجراء — فلا يُؤتمت إلا أكبرها، وما يُبنى لا يتعلم من تشغيله شيئًا. مُنجِز وكيل واحد يتقنها كلها لأن كل إجراء عنده مهارةٌ محوكمة — ويتحسن كل أسبوع لأن له ذاكرة ومراجعًا.»

Show **الحوكمة**: skill cards with versions, the learning strip (memory meter, proposal counts). «هذه ليست وثائق؛ هذه الصلاحيات المنفَّذة وعدّادات التعلّم.»

### [0:40–2:30] المعاملة الأولى — إجازة أحمد، بخيارات لا أسئلة

As أحمد, type: «أريد إجازة». Narrate what judges see:
- the router picks **leave-request** and the agent replies with **tap-to-answer chips**: سنوية / مرضية / طارئة — tap سنوية;
- it offers **computed date ranges** («من … إلى … — ٥ أيام عمل») — tap one;
- it already knows his remaining balance (it fetched it itself) and — memory beat — asks to confirm dates **بالتقويم الميلادي**: *«لم يخبره أحدٌ اليوم بذلك — الذاكرة المؤسسية تسجل أن أحمد يفضّل هذا».*
- the preview card: fields, working days (weekend skipped — invite judges to count), approval chain → **تأكيد**.

Switch persona to نورة? No — أحمد's manager is مريم: switch to **مريم** → **الاعتمادات** → the request card leads with **تقرير الوكيل للمعتمِد**: الموظف — الطلب — التحقق (الرصيد، التعارضات) — التوصية. Approve with a note. Back as أحمد: balance dropped.

> «الموظف لم يفتح نموذجًا، والمديرة لم تقرأ نموذجًا خامًا — قرأت تقرير تحققٍ جاهزًا وقررت في ثوانٍ.»

### [2:30–3:40] الشهادة الفورية + PDF المختوم + برهان الحوكمة

As أحمد: «أحتاج شهادة راتب» → chips for the addressee (بنوك تجريبية، سفارة، لمن يهمه الأمر، أخرى…) → preview → confirm → executed instantly with a CERT number. Open **طلباتي** → **تنزيل الشهادة (PDF)** → the sealed, watermarked A4 opens print-ready. *«شهادة رسمية بختم الجهة — والعلامة المائية "تجريبي" لأن بياناتنا كلها وهمية».*

Then the governance money-shot — in the same certificate chat ask: «بالمناسبة كم رصيد إجازتي؟»

> The gateway REFUSES — this skill's allowlist has no get_leave_balance. Open **الحوكمة** → the red **DENIED** row. «الوكيل نفسه لا يستطيع تجاوز مهارته. ولاحظوا: الأخطاء العادية تظهر ERROR — الشارة الحمراء للرفض الحوكمي حصرًا.»

### [3:40–5:10] التعلّم المحوكم — the killer beat

> «أهم سؤال في أي نظام ذكاء اصطناعي حكومي: هل يتعلم؟ ومن يملك قرار التعلّم؟»

1. Fire the reflection pass (`POST /munjiz/reflect` button or webhook). It reads the recent transactions **after the employees were served**, writes a declarative memory fact, and **proposes** a skill improvement — nothing changes yet.
2. Open **الحوكمة**: the proposal card sits **pending** with the agent's rationale. «الوكيل يقترح فقط — لا يملك خدمة تكتب في المهارات أصلًا؛ البوابة تمنعه.»
3. As the procedure's owner, tap **اعتماد التحسين** → the skill card's **version bumps on screen** (e.g. expense-claim 1.0.2 → 1.0.3). Open the skill: the approved rule is written into its body with the patch id, the approver, and the date.

> «اقترح النظام تحسين إجرائه من تشغيله الفعلي، واعتمده مالك الإجراء بنقرة، فارتفع الإصدار — تحسّن حقيقي، وقرار بشري بالكامل، وأثر مُدقَّق.»

### [5:10–6:00] حارس الإنجاز

Fire the sweep (فحص المواعيد button). The stale seeded claim triggers: the model **chooses** remind/escalate with a written justification → audit rows land. «لا معاملة تعلق في درج أحد — والجدولة تعمل وحدها؛ أطلقتها يدويًا كي لا ننتظر.»

### [6:00–7:15] فحص اللجنة — داخل n8n

Open the leave execution in n8n: the think plan, the sequence of call_service choices, the deterministic working-day cross-check, the composed system prompt showing the skill body + the **learned layer** + memory. Show the credentials manager: one key, nowhere else. Show the Skills data table: `created_by: human`, versions.

> «المهارة من جدول محوكم، القرار من النموذج، البوابة تسجل كل شيء — ولا مفتاح خارج مدير بيانات الاعتماد.»

### [7:15–8:00] الخاتمة

> «إجراء اعتيادي: من نموذج يُرفض بعد أيام إلى محادثة بخيارات جاهزة. المعتمِد: من نموذج خام إلى تقرير تحققٍ مُعدّ. النظام: من أتمتةٍ تتقادم إلى منظومة تقترح تحسين نفسها ويعتمدها الإنسان. مُنجِز ليس روبوت محادثة — إنه موظف خدمات يتقن كل إجراء، ويتعلم تحت الحوكمة.»

Invite a judge: pick any persona, try a request, or ask the certificate agent for something outside its skill and watch governance say no.

## Contingencies

| Risk | Response |
|---|---|
| Gemini free-tier 429 | The binding constraint. **Enable billing on the AI Studio project before demo day** (stays free at this volume) or bring a fresh key; never rehearse on the demo key the same day. Retries with backoff are narratable self-correction. |
| Router mismatch on odd phrasing | Tap the service card in the sidebar (pre-fills the request), or rephrase naturally. |
| A beat stalls | The reflection and sweep beats are independently skippable; the approval + certificate + denial trio is the core. Rehearse to 7:30. |
| Network death | Everything is localhost except Gemini itself — hotspot fallback; a cached successful execution open in tab 3. |
| Projector font too small | The portal is legible at 125% browser zoom without breaking layout. |
