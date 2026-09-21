---
name: open-code-review
description: "Review diff Git theo ruleset rõ (bug, bảo mật, hiệu năng): CLI ocr hoặc cùng khung nếu chưa cài."
description_en: "Review Git diffs with a clear ruleset (bug, security, perf): ocr CLI or the same frame if missing."
group: "AI & Hệ thống"
license: Apache-2.0
metadata:
  version: "1.0"
  upstream: "https://github.com/alibaba/open-code-review"
---

# Review code theo ruleset (open-code-review)

## Dùng để làm gì

Soát **thay đổi Git** (working copy, commit, nhánh) thành nhận xét **theo dòng**, có:

- **Ruleset** theo loại file (null, XSS, SQL, race, test thiếu…)
- **Mức:** critical / high / medium / low
- **Nhóm:** bug / security / performance / maintainability / test / style / documentation

Rút từ [alibaba/open-code-review](https://github.com/alibaba/open-code-review) (`ocr` CLI). Javis **không** ship binary; skill dạy quy trình + khung ruleset Javis (`references/ruleset.md`).

## Khi nào dùng

- «review PR», «soi diff», «code review trước merge», «ocr», «ruleset review»

**Không dùng** thay cho brainstorm/plan trước khi viết code (`brainstorming`, `writing-plans`). Không dùng để pentest hệ thống ngoài repo đang mở.

## Chuẩn bị

1. Đang ở **git repo** đúng (hoặc `--repo` nếu CLI).
2. Chốt phạm vi: working copy / một commit / `main...HEAD`.
3. Đọc `references/ruleset.md` (luôn). Có CLI thì dùng thêm ruleset của ocr.

```bash
command -v ocr
```

- Có `ocr`: ưu tiên CLI (bước dưới).
- **Chưa cài:** **fallback** - agent tự review theo cùng khung severity + ruleset.md. **Không tự** `npm i -g`. Chỉ cài khi user đồng ý.

## Cách chạy (khi có ocr)

```bash
ocr review --audience agent --background "ngữ cảnh nghiệp vụ ngắn" 
# PR:  --from main --to HEAD
# commit: --commit <sha>
# xem file nào: --preview
```

Ngôn ngữ comment: nhờ user, mặc định tiếng Việt trong báo cáo Javis.

Ruleset user (nếu có file dự án): `--rule`, rồi `.opencodereview/rule.json`, rồi mặc định ocr. Chi tiết flag: `ocr review --help` (đừng bịa flag).

## Quy trình (mọi đường)

1. Tóm 2-4 câu **ngữ cảnh** (tính năng / rủi ro).
2. Review từng file khớp ruleset (không soi generated / lockfile trừ khi user bảo).
3. Bỏ `low` kiểu nitpick trừ khi user xin soi style.
4. Báo cáo:

```markdown
## Code review

**Phạm vi:** …
**Ruleset:** Javis `references/ruleset.md` (+ ocr nếu có)
**Số issue:** X critical, Y high, Z medium

### Critical
- `file:dòng` [security|bug] - mô tả. Gợi ý sửa.

### High
…

### Medium
…
```

5. Chỉ **sửa code** khi user nói «review rồi sửa».

## Bẫy

- Không bịa lỗ hổng không có trong diff.
- Không dump cả patch. Chỉ dòng + lý do.
- Engine API không shell: fallback ruleset, nói rõ không chạy được `ocr`.
- Không copy nguyên SKILL.md Alibaba vào vault.

## Kiểm chứng

- [ ] Có bảng critical/high/medium (hoặc «không có issue ≥ medium»)
- [ ] Mỗi mục có path + category
- [ ] Đã ghi ruleset nào dùng
