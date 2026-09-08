"""OpenMAIC: tự chọn lop-hoc.md khi slug thiếu tiền tố (marketing-thuc-chien → digital-…)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from openmaic_paths import pick_best_lop_hoc, score_lop_hoc_candidates  # noqa: E402


CANDS = [
    "exports/bai-giang/digital-marketing-thuc-chien/lop-hoc.md",
    "exports/bai-giang/marketing-can-ban/lop-hoc.md",
    "exports/bai-giang/seo-co-ban/lop-hoc.md",
]


def test_suffix_slug_picks_digital():
    wanted = "exports/bai-giang/marketing-thuc-chien/lop-hoc.md"
    pick = pick_best_lop_hoc(wanted, CANDS)
    assert pick == "exports/bai-giang/digital-marketing-thuc-chien/lop-hoc.md", pick


def test_exact_folder_wins():
    wanted = "exports/bai-giang/marketing-can-ban/lop-hoc.md"
    pick = pick_best_lop_hoc(wanted, CANDS)
    assert pick == "exports/bai-giang/marketing-can-ban/lop-hoc.md", pick


def test_unrelated_no_guess():
    wanted = "exports/bai-giang/toan-lop-1/lop-hoc.md"
    pick = pick_best_lop_hoc(wanted, CANDS)
    assert pick is None, pick


def test_marketign_scores_marketing_folder():
    wanted = "exports/bai-giang/digital-marketign-thuc-chien/lop-hoc.md"
    ranked = score_lop_hoc_candidates(wanted, CANDS)
    assert ranked[0][1].endswith("digital-marketing-thuc-chien/lop-hoc.md"), ranked


if __name__ == "__main__":
    test_suffix_slug_picks_digital()
    test_exact_folder_wins()
    test_unrelated_no_guess()
    test_marketign_scores_marketing_folder()
    print("ok")
