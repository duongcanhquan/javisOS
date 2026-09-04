# Upstream: dzhng/deep-research (Open Deep Research)

Nguồn: https://github.com/dzhng/deep-research (MIT)

## Ý tưởng cốt lõi

Nghiên cứu lặp theo **breadth** (số query SERP mỗi vòng) và **depth** (số vòng đào sâu):

1. Query + follow-up làm rõ hướng
2. Sinh SERP queries (mỗi cái kèm researchGoal)
3. Search + đọc nội dung → learnings (dày thông tin, có entity/metrics) + followUpQuestions
4. Nếu depth > 0: lấy hướng mới + learnings cũ → vòng mới (breadth thu hẹp dần, thường `ceil(breadth/2)`)
5. Viết report markdown dài + mục Sources (URL đã thăm)

## Chạy CLI gốc (tuỳ chọn)

Cần Node 22, `FIRECRAWL_KEY`, `OPENAI_KEY` (hoặc Fireworks/R1 / endpoint local):

```bash
git clone https://github.com/dzhng/deep-research.git
cd deep-research && npm i
# .env.local với FIRECRAWL_KEY + OPENAI_KEY
npm start
```

Trên Javis mặc định **không** phụ thuộc Firecrawl: dùng Tavily MCP / WebSearch theo `SKILL.md`.
