---
name: cherry-pick-agent-skills
description: "Cherry-pick đúng một SKILL.md từ kho agent-skills, viết lại chuẩn Javis; cấm import cả repo."
description_en: "Cherry-pick one SKILL.md from an agent-skills catalog, rewrite to Javis format; never import the whole repo."
group: "AI & Hệ thống"
metadata:
  version: "1.0"
---

# Cherry-pick skill từ kho agent-skills

## Dùng để làm gì

Lấy **từng** kỹ năng từ kho cộng đồng (Vercel, Tech Leads Club, skills.sh…), **viết lại** thành skill Javis (`description` ≤150, `group`, mục Khi nào dùng).

**Cấm import cả kho.** Một folder `SKILL.md` một lần. Không copy nguyên văn dài.

## Khi nào dùng

- «lấy skill từ vercel-labs/agent-skills», «cherry-pick SKILL.md», «đừng cài cả repo skills»
- `find-skills` đã tìm thấy một skill ngoài, user muốn **nhét vào Javis** (không phải chỉ `npx skills add` cho Cursor)

**Không dùng** khi user chỉ hỏi «có skill nào trên skills.sh không» → `find-skills`.
**Không dùng** để tạo năng lực Javis từ đầu → `javis-builder`.

## Chuẩn bị

1. Chốt **đúng một** skill (slug + URL raw `SKILL.md`). Chưa chốt thì liệt kê 3 ứng viên, hỏi 1 câu.
2. Đọc folder `.claude/skills/` và `skills/` brain: trùng năng lực thì **cập nhật skill cũ**, không đẻ bản sao.
3. Nguồn thường gặp (chỉ để tìm, không clone cả repo):

| Kho | Ghi chú |
|---|---|
| https://github.com/vercel-labs/agent-skills | React/Next, web-design… |
| https://github.com/tech-leads-club/agent-skills | Registry + CLI; cài từng `--skill` |
| https://skills.sh | Tra cứu, rồi lấy đúng một package |

## Quy trình

1. Fetch **một** `SKILL.md` (WebFetch / raw GitHub). Không `git clone` cả monorepo.
2. Tóm 5-10 dòng: skill gốc dùng để làm gì, khi nào, cấm gì.
3. Viết file mới `skills/<slug-ascii>/SKILL.md` theo `javis-builder`:
   - `description` nêu thẳng năng lực, **đếm ≤150** ký tự; có `description_en`
   - `group` bắt buộc
   - Thân: Khi nào dùng / Chuẩn bị / Cách chạy / Bẫy / Kiểm chứng
   - Không em dash
4. Script/reference gốc: chỉ copý **công cụ ngắn** (vài chục dòng) nếu cần chạy; tài liệu dài thì tóm + link upstream.
5. Ghi `metadata.upstream` = URL file gốc.
6. Báo user: slug, dùng để làm gì (1 câu), khác skill nào sẵn có.

## Bẫy

- **Cấm import cả kho** (`npx skills add owner/repo` không kèm `@tên-skill` rồi copy hết vào vault).
- Cấm dán nguyên văn SKILL.md dài vào Javis (bản quyền + token). **Viết lại**.
- Cấm pentest / leak prompt / tải khóa học trả phí dù kho ngoài có.
- Cấm skill router chỉ «xem skill X».

## Kiểm chứng

- [ ] Đúng một slug mới hoặc một file cũ được sửa
- [ ] `description` đã đếm ≤150
- [ ] Có `upstream` + câu «dùng để làm gì»
