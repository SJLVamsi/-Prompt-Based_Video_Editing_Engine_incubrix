"""Burn-in guard: agrees with `ffmpeg -filters`, raises actionable error when blocked."""
from backend.engine.render import ffmpeg as F


def test_guard_agrees_with_binary(tmp_path):
    import shutil
    if shutil.which("ffmpeg") is None:
        assert F.ffmpeg_has_filter("anything") is False
        return
    assert F.ffmpeg_has_filter("scale") is True
    assert F.ffmpeg_has_filter("trim") is True
    assert F.ffmpeg_has_filter("concat") is True
    # this environment's brew build lacks text filters; elsewhere they may exist
    if not F.ffmpeg_has_filter("subtitles"):
        try:
            F.require_text_burnin()
            raise AssertionError("should have raised")
        except RuntimeError as e:
            assert "libass" in str(e) and "mov_text" in str(e)
    else:
        F.require_text_burnin()  # passes where libass exists


def test_guard_false_without_binary(monkeypatch):
    import subprocess
    def boom(*a, **k):
        raise OSError("no ffmpeg")
    monkeypatch.setattr(subprocess, "run", boom)
    assert F.ffmpeg_has_filter("scale") is False
