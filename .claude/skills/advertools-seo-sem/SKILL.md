---
name: Advertools SEO/SEM
description: "Dùng advertools (pip) sinh keyword, sitemap, robots, crawl SEO; xuất CSV exports/marketing."
description_en: "Use advertools (pip) for keywords, sitemap, robots, SEO crawl; export CSV to exports/marketing."
group: Marketing
---

# Advertools (SEO / SEM)

Hướng dẫn dùng thư viện Python **advertools** trên host/VPS khi đã cài - **không** vendor vào image Docker Javis.

## When to use

- Sinh biến thể từ khóa SEM, đọc sitemap/robots, crawl on-page cơ bản, phân tích URL.
- User có shell trên máy chạy Javis / VPS và chấp nhận `pip install`.

## Cài đặt (host/VPS)

```bash
pip install advertools
# hoặc: python3 -m pip install --user advertools
```

Không thêm package này vào Dockerfile mặc định trừ khi ops quyết định riêng.

## Việc thường dùng

| Việc | Hướng gọi (gợi ý) |
|------|-------------------|
| Keyword expand | `adv.kw_generate(...)` / helpers từ khóa trong docs |
| Sitemap | `adv.sitemap_to_df(url)` |
| Robots | `adv.robotstxt_to_df(url)` |
| Crawl nhẹ | `adv.crawl(url_list, output_file=...)` rồi đọc DataFrame |

Chi tiết API: [eliasdabbas/advertools](https://github.com/eliasdabbas/advertools) (MIT). Đọc README/docs khi tham số đổi theo version.

## Quy trình Javis

1. Xác nhận package import được (`python3 -c "import advertools"`).
2. Chạy script ngắn trong workspace/shell (không crawl site người khác trái phép; tôn trọng robots + rate).
3. Xuất CSV/Parquet vào `exports/marketing/<slug>/` (vd. `sitemap.csv`, `crawl.csv`, `keywords.csv`).
4. Tóm tắt insight ngắn trong chat + link file; audit nội dung sâu → `kiem-tra-seo` / `seo-gpt`.

## Không làm

- Không cài mặc định vào container production qua skill này.
- Không thay crawler doanh nghiệp / Search Console API nếu user đã có MCP phù hợp hơn.

## Nguồn

Skill hướng dẫn dựa trên [advertools](https://github.com/eliasdabbas/advertools) (MIT). Javis không ship mã thư viện.
