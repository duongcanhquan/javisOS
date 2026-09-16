# Pattern AI-tell (rút gọn)

Nguồn gốc: catalog 55 pattern của
[Aboudjem/humanizer-skill](https://github.com/Aboudjem/humanizer-skill) (MIT),
rút gọn cho Javis. Khi cần sâu hơn, mở upstream `references/patterns.md`.

Gốc Wikipedia: [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).

## P1-P30 (lõi)

| ID | Tên | Trigger / sửa nhanh |
|----|-----|---------------------|
| P1 | Significance inflation | testament, pivotal, evolving landscape → nêu việc cụ thể |
| P2 | Name-drop notability | featured in NYT/BBC… → một nguồn + nội dung thật |
| P3 | Superficial -ing | highlighting, fostering, showcasing → cắt hoặc biến thành câu có nguồn |
| P4 | Promotional | nestled, breathtaking, cutting-edge, seamless → fact |
| P5 | Vague attribution | experts argue, research suggests → tên nguồn hoặc cắt |
| P6 | Formulaic challenges | Despite… faces challenges… future looks → số liệu hoặc cắt |
| P7 | AI vocabulary | delve, leverage, tapestry, realm, moreover, furthermore → plain words |
| P8 | Copula avoidance | serves as / boasts / features → is / has |
| P9 | Negative parallelism | not only X but Y (lặp) → nói thẳng |
| P10 | Rule of three | ba danh từ trừu tượng ép → số lượng tự nhiên |
| P11 | Synonym cycling | cùng entity đổi tên liên tục → một thuật ngữ |
| P12 | False ranges | from X to Y không cùng thang → liệt kê thật |
| P13 | Em dash | U+2014 → dấu phẩy / hai chấm / gạch nối |
| P14 | Bold / emoji format | bold dày, emoji tiêu đề → bớt |
| P15 | List syndrome | bullet `**Header:**` thay prose → viết đoạn |
| P16 | Title Case headings | Strategic Negotiations… → sentence case |
| P17 | Curly quotes | “ ” khi author dùng " " → khớp author |
| P18 | Formal register | it should be noted that → plain |
| P19 | Chatbot artifacts | I hope this helps, Certainly!, Here is a → cắt |
| P20 | Cutoff disclaimer | as of my last training → fact hoặc cắt |
| P21 | Sycophantic | Great question!, Absolutely! → trả lời thẳng |
| P22 | Filler | in order to, due to the fact that, it's worth noting → rút |
| P23 | Excess hedging | could potentially possibly → một mức chắc |
| P24 | Generic positive end | future looks bright → fact cuối |
| P25 | Hallucination markers | số/ngày quá chắc không nguồn → verify hoặc cắt |
| P26 | Perfect/error mix | đoạn hoàn hảo xen lỗi sơ → một mức chất lượng |
| P27 | Question H2 spam | What makes X unique? dày đặc → heading khẳng định |
| P28 | Markdown bleeding | `**bold**` trong email/Word → strip |
| P29 | Overview opening | In this article we will explore → vào thẳng nội dung |
| P30 | Uniform length | mọi câu 15-25 từ → trộn ngắn/dài |

## P31-P43 (emerging)

P31 noun-phrase cycling · P32 chat framing in articles · P33 `[Your Name]` placeholders ·
P34 citeturn0 / oaicite / grok_card · P35 utm_source=chatgpt · P36 register shift ·
P37 source-list as content · P38 shuffleable paragraphs · P39 Whether… closers ·
P40 symbolizes/embodies gloss · P41 The kicker? · P42 erratic inline bold ·
P43 treadmill / In other words restates

## P44-P55 (craft / forensic)

P44 false agency («the data tells us») · P45 distant narrator · P46 diff-anchored docs ·
P47 hyphen pair after verb · P48 aphorism formulas · P49 heading + echo line ·
P50 agentless passive · P51 CoT leak (Let me think / Step 1) · P52 unicode obfuscation ·
P53 HC3 hedged openers (There are several ways…) · P54 argument residue ·
P55 leftover hedge debris

## Tiếng Việt - cluster hay gặp

| Dấu | Ví dụ | Sửa |
|-----|--------|-----|
| Mở bài sáo | Trong bối cảnh hiện nay… | Vào thẳng việc / số |
| Song song dịch | Không chỉ… mà còn… (lặp) | Một ý chính |
| Kết đoạn SEO | Tóm lại, mở ra nhiều cơ hội | Fact hoặc câu hỏi mở |
| Từ đệm | Đáng chú ý là, Không thể phủ nhận rằng | Cắt |
| Anh cứng trong bài Việt | Moreover, Furthermore, leverage | Hơn nữa / dùng / bỏ |
| Ba cụm trừu tượng | đổi mới, sáng tạo và phát triển bền vững | Việc cụ thể |

## Guardrails (nhắc lại)

- Flag **cụm**, không flag một lần xuất hiện.
- Văn L2 / formal ≠ AI.
- Giữ số, tên, ngày, trích dẫn nguồn.
- Không chứng minh tác giả - chỉ ước lượng dấu viết.
