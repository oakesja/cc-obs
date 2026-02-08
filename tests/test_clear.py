import pytest

from cc_obs.commands.clear import run


def test_clear_deletes_files(project_dir, events_file):
    events_file.write_text("data\n")
    view_html = project_dir / ".claude" / "cc-obs" / "view.html"
    view_html.write_text("<html></html>")

    run()

    assert not events_file.exists()
    assert not view_html.exists()


def test_clear_nothing_to_clear(project_dir, capsys):
    run()
    assert "Nothing to clear" in capsys.readouterr().out


def test_clear_quiet(project_dir, events_file, capsys):
    events_file.write_text("data\n")
    run(quiet=True)
    assert not events_file.exists()
    assert capsys.readouterr().out == ""


def test_clear_no_project_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 1


def test_clear_quiet_no_project_root(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(quiet=True)
    # No crash, no output
    assert capsys.readouterr().out == ""
