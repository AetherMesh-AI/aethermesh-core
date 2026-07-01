from scripts.mutmut_early_fail import (
    format_duration,
    format_progress_line,
    max_non_killed_for_score,
    parse_mutmut_counts,
    parse_mutmut_progress,
)


def test_progress_parser_uses_complete_mutmut_status_lines() -> None:
    line = "⠸ 49/6647  🎉 48 🫥 0  ⏰ 2  🤔 3  🙁 4"

    assert parse_mutmut_counts(line) == (
        49,
        6647,
        {"killed": 48, "timeout": 2, "suspicious": 3, "survived": 4},
    )
    assert parse_mutmut_progress(line) == (49, 6647, 9)
    assert parse_mutmut_progress("⠸ 50/6") == (None, None, 0)


def test_score_threshold_math_stays_strict() -> None:
    assert max_non_killed_for_score(6647, 95) == 332
    assert max_non_killed_for_score(6639, 95) == 331


def test_progress_line_reports_speed_eta_and_emoji_counts() -> None:
    line = format_progress_line(
        done=50,
        total=100,
        counts={"killed": 45, "timeout": 1, "suspicious": 2, "survived": 3},
        elapsed_seconds=10,
    )

    assert "50/100" in line
    assert "🎉 45" in line
    assert "⏰ 1" in line
    assert "🤔 2" in line
    assert "🙁 3" in line
    assert "Mut/s 5.00" in line
    assert "Est. 10s" in line


def test_duration_format_is_compact() -> None:
    assert format_duration(None) == "unknown"
    assert format_duration(9.4) == "9s"
    assert format_duration(70) == "1m10s"
    assert format_duration(3671) == "1h01m11s"
