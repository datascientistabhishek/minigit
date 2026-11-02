"""Tests for what ``minigit status`` prints."""

from minigit.refs import head_commit, set_head


def test_clean_repository(repo, run, write):
    write("a.txt", "a\n")
    run("add", "a.txt")
    run("commit", "-m", "first")
    result = run("status")
    assert result.code == 0
    assert result.out == "On branch main\nnothing to commit, working tree clean\n"


def test_empty_repository_says_no_commits_yet(repo, run):
    out = run("status").out
    assert out.startswith("On branch main\n\nNo commits yet\n")
    assert "nothing to commit, working tree clean" in out


def test_staged_section(repo, run, write):
    write("notes.txt", "n\n")
    run("add", "notes.txt")
    out = run("status").out
    assert "Changes to be committed:" in out
    assert "\tnew file:   notes.txt" in out


def test_all_three_sections(repo, run, write):
    write("hello.txt", "hello\n")
    write("old.txt", "old\n")
    run("add", "hello.txt", "old.txt")
    run("commit", "-m", "first")

    write("hello.txt", "staged edit\n")
    run("add", "hello.txt")
    write("hello.txt", "unstaged edit\n")
    (repo.worktree / "old.txt").unlink()
    write("scratch.py", "print(1)\n")

    out = run("status").out
    assert "\tmodified:   hello.txt" in out
    assert "\tdeleted:    old.txt" in out
    assert "\tscratch.py" in out
    assert out.index("Changes to be committed:") < out.index("Changes not staged for commit:")
    assert out.index("Changes not staged for commit:") < out.index("Untracked files:")


def test_detached_head(repo, run, write):
    write("a.txt", "a\n")
    run("add", "a.txt")
    run("commit", "-m", "first")
    commit = head_commit(repo)
    set_head(repo, commit, symbolic=False)
    assert run("status").out.startswith(f"HEAD detached at {commit[:7]}")


def test_status_background_colors_when_tty(repo, run, write, monkeypatch):
    """Untracked files get red background, tracked files get green background."""
    write("tracked_committed.txt", "initial\n")
    run("add", "tracked_committed.txt")
    run("commit", "-m", "first")

    write("tracked_staged.txt", "new staged\n")
    run("add", "tracked_staged.txt")

    write("tracked_committed.txt", "modified content\n")
    write("untracked.txt", "untracked\n")

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    out = run("status").out

    # Tracked files (staged and unstaged) have green background (\033[42m...\033[0m)
    assert "\tnew file:   \033[42mtracked_staged.txt\033[0m" in out
    assert "\tmodified:   \033[42mtracked_committed.txt\033[0m" in out

    # Untracked files have red background (\033[41m...\033[0m)
    assert "\t\033[41muntracked.txt\033[0m" in out

    # Background color is applied ONLY to the path, not the label prefix or entire line
    assert "\033[42m\tnew file:" not in out
    assert "\033[41m\t" not in out


def test_status_no_color_flag_suppresses_background_color(repo, run, write, monkeypatch):
    write("tracked.txt", "hello\n")
    run("add", "tracked.txt")
    write("untracked.txt", "untracked\n")

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    out = run("--no-color", "status").out
    assert "\033[41m" not in out
    assert "\033[42m" not in out
    assert "\tnew file:   tracked.txt" in out
    assert "\tuntracked.txt" in out
