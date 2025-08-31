import main


def test_select_font_path(monkeypatch, tmp_path):
    gothic = tmp_path / "GenEiMGothic2-Regular.ttf"
    gothic.touch()
    mincho = tmp_path / "GenEiChikugoMin3-R.ttf"
    mincho.touch()
    monkeypatch.setattr(main, "FONT_MAP", {"gothic": gothic, "mincho": mincho})

    assert main.select_font_path("gothic") == str(gothic)
    assert main.select_font_path("mincho") == str(mincho)
    assert main.select_font_path("unknown") is None
    assert main.select_font_path(None) is None
