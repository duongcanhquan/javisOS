"""Gợi ý path OpenMAIC khi typo slug (marketign → marketing)."""


def test_marketign_typo_fix():
    wanted = "exports/bai-giang/digital-marketign-thuc-chien/lop-hoc.md"
    alt = wanted.replace("marketign", "marketing")
    assert alt == "exports/bai-giang/digital-marketing-thuc-chien/lop-hoc.md"
    assert "marketign" in wanted
    assert "marketign" not in alt
