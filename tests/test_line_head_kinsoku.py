import main
import pytest


def _get_generator() -> main.JapaneseVerticalHTMLGenerator:
    return main.JapaneseVerticalHTMLGenerator()


@pytest.mark.parametrize("punct", ["、", "。", "」", "〟"])
def test_kinsoku_punctuation(punct):
    gen = _get_generator()
    text = f"テスト{punct}テスト"
    result = gen._apply_budoux_line_breaks(text, max_chars_per_line=3)
    lines = result.split("\n")
    assert all(not line.startswith(punct) for line in lines[1:])
    assert lines[0].endswith(punct)


def test_kinsoku_sokuon():
    gen = _get_generator()
    lines = ["あああああ", "っああああ"]
    adjusted = gen._apply_line_head_kinsoku(lines)
    assert adjusted == ["あああああっ", "ああああ"]
