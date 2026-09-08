#pytest tests/test_logging.py -v
import re

from wallpaper.logging import debug_log


def test_debug_false_prints_nothing(capsys):
    debug_log(
        "YOU SHOULD NOT SEE ME",
        debug=False,
    )

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


def test_debug_true_prints_message(capsys):
    debug_log(
        "hello creatures",
        debug=True,
    )

    captured = capsys.readouterr()

    assert captured.out == "hello creatures\n"


def test_debug_false_does_not_create_log_file(tmp_path):
    log_path = tmp_path / "debug.log"

    debug_log(
        "nope",
        debug=False,
        log_path=log_path,
    )

    assert not log_path.exists()


def test_debug_true_writes_to_log_file(tmp_path):
    log_path = tmp_path / "debug.log"

    debug_log(
        "wallpaper changed",
        debug=True,
        log_path=log_path,
    )

    assert log_path.exists()

    contents = log_path.read_text(
        encoding="utf-8"
    )

    assert "wallpaper changed" in contents


def test_log_entry_contains_timestamp(tmp_path):
    log_path = tmp_path / "debug.log"

    debug_log(
        "timestamp test",
        debug=True,
        log_path=log_path,
    )

    contents = log_path.read_text(
        encoding="utf-8"
    )

    assert re.fullmatch(
        r"\[\d{4}-\d{2}-\d{2} "
        r"\d{2}:\d{2}:\d{2}\] "
        r"timestamp test\n",
        contents,
    )


def test_multiple_messages_are_appended(tmp_path):
    log_path = tmp_path / "debug.log"

    debug_log(
        "first",
        debug=True,
        log_path=log_path,
    )

    debug_log(
        "second",
        debug=True,
        log_path=log_path,
    )

    contents = log_path.read_text(
        encoding="utf-8"
    )

    assert "first" in contents
    assert "second" in contents

    assert contents.count("\n") == 2