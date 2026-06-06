from cd_ripper.organizer import (
    _build_target_filename,
    _normalize_track_number,
    _sanitize_title,
)


def test_normalize_track_number():
    assert _normalize_track_number("1/13") == "01"
    assert _normalize_track_number("10") == "10"
    assert _normalize_track_number(" 3 ") == "03"
    assert _normalize_track_number(None) is None


def test_sanitize_title():
    assert _sanitize_title("No / Parachutes") == "No Parachutes"
    assert _sanitize_title("I’m Alive") == "I’m Alive"
    assert _sanitize_title('Track: "Hello"?') == "Track Hello"


def test_build_target_filename():
    assert _build_target_filename("Dizzy", "03", "track03.cdda.wav") == "03 - Dizzy.wav"
    assert _build_target_filename("Angel", None, "track09.cdda.wav") == "Angel.wav"
    assert _build_target_filename(None, "11", "track11.cdda.wav") == "11 - track11.cdda.wav"
    assert _build_target_filename(None, None, "track12.cdda.wav") == "track12.cdda.wav"
