import pytest
import unicodedata
from types import SimpleNamespace

from src.data.card_data_downloader import CardDataDownloader




@pytest.mark.parametrize(
    "name,expected",
    [
        # Happy path: simple name
        ("Sol Ring", "sol-ring"),
        # Happy path: name with multiple spaces
        ("Arcane Signet", "arcane-signet"),
        # Happy path: name with mixed case
        ("Teferi's Protection", "teferi's-protection"),
        # Happy path: name with dash
        ("Sword of Fire and Ice", "sword-of-fire-and-ice"),
        # Happy path: name with numbers
        ("Channel 2021", "channel-2021"),
        # Happy path: name with apostrophe
        ("Gideon's Intervention", "gideon's-intervention"),
        # Happy path: name with comma
        ("Karn, the Great Creator", "karn,-the-great-creator"),
        # Happy path: name with slash
        ("Fire // Ice", "fire-//-ice"),
        # Happy path: name with parentheses
        ("Nissa, Who Shakes the World (Promo)", "nissa,-who-shakes-the-world-(promo)"),
        # Happy path: name with non-ASCII (accents)
        ("Élan Vital", "elan-vital"),
        # Happy path: name with non-ASCII (umlaut)
        ("Jötun Grunt", "jotun-grunt"),
        # Happy path: name with ligature
        ("Æther Vial", "aether-vial"),
        # Happy path: name with cedilla
        ("Façade", "facade"),
        # Happy path: name with tilde
        ("Señor of the Wilds", "senor-of-the-wilds"),
        # Edge case: empty string
        ("", ""),
        # Edge case: only spaces
        ("   ", "---"),
        # Edge case: only non-ASCII
        ("ÆÉÖçñ", "aeeocn"),
        # Edge case: only special characters
        ("!@#$%^&*()", "!@#$%^&*()"),
        # Edge case: already formatted
        ("already-formatted", "already-formatted"),
        # Edge case: single character
        ("A", "a"),
        # Edge case: single non-ASCII character
        ("É", "e"),
        # Edge case: whitespace at ends
        ("  Sol Ring  ", "--sol-ring--"),
        # Edge case: tab and newline
        ("Sol\tRing\n", "sol\tring\n"),
    ],
    ids=[
        "simple_name",
        "multiple_spaces",
        "mixed_case",
        "with_dash",
        "with_numbers",
        "with_apostrophe",
        "with_comma",
        "with_slash",
        "with_parentheses",
        "with_accent",
        "with_umlaut",
        "with_ligature",
        "with_cedilla",
        "with_tilde",
        "empty_string",
        "only_spaces",
        "only_non_ascii",
        "only_special_chars",
        "already_formatted",
        "single_char",
        "single_non_ascii",
        "whitespace_ends",
        "tab_and_newline",
    ],
)
def test_format_name_for_edhrec_happy_and_edge_cases(name, expected):
    # Arrange

    downloader = CardDataDownloader()

    # Act

    result = downloader._format_name_for_edhrec(name)

    # Assert

    assert result == expected


@pytest.mark.parametrize(
    "name,expected_exception",
    [
        # Error case: None as input
        (None, TypeError),
        # Error case: integer as input
        (123, TypeError),
        # Error case: list as input
        (["Sol Ring"], TypeError),
        # Error case: dict as input
        ({"name": "Sol Ring"}, TypeError),
        # Error case: bytes as input
        (b"Sol Ring", TypeError),
    ],
    ids=[
        "none_input",
        "int_input",
        "list_input",
        "dict_input",
        "bytes_input",
    ],
)
def test_format_name_for_edhrec_error_cases(name, expected_exception):
    # Arrange

    downloader = CardDataDownloader()

    # Act & Assert

    with pytest.raises(expected_exception):
        downloader._format_name_for_edhrec(name)
