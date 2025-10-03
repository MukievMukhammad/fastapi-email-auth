import pytest

from src.fastapi_email_auth.utils.bip39 import (
    BIP39Generator,
    generate_code,
    validate_code,
)


def test_generate_english_default():
    """Generate English code by default"""
    code = generate_code()
    words = code.split()
    assert len(words) == 2


def test_generate_russian_with_hyphen():
    """Generate Russian code with hyphen separator"""
    code = generate_code(2, "russian", "-")
    words = code.split("-")
    assert len(words) == 2


def test_generate_various_word_counts():
    """Support various word counts"""
    for count in [1, 2, 3, 4, 5]:
        code = generate_code(count)
        assert len(code.split()) == count


def test_invalid_word_count():
    """Reject invalid word counts"""
    with pytest.raises(ValueError, match="must be between 1 and 12"):
        generate_code(0)

    with pytest.raises(ValueError, match="must be between 1 and 12"):
        generate_code(13)


def test_validate_english():
    """Validate English codes"""
    assert validate_code("abandon ability")
    assert validate_code("wrong invalid")


def test_validate_russian():
    """Validate Russian codes"""
    code = generate_code(2, "russian")
    assert validate_code(code, "russian")


def test_validate_with_separator():
    """Validate codes with custom separator"""
    code = generate_code(2, "russian", "-")
    assert validate_code(code, "russian", "-")


def test_multiple_languages():
    """Test various supported languages"""
    languages = ["english", "russian", "french", "spanish", "japanese"]

    for lang in languages:
        code = generate_code(2, lang)
        assert validate_code(code, lang)


def test_unsupported_language():
    """Reject unsupported languages"""
    with pytest.raises(ValueError, match="Unsupported language"):
        BIP39Generator("klingon")


def test_entropy_calculation():
    """Calculate entropy correctly"""
    generator = BIP39Generator()

    entropy_2 = generator.get_entropy_bits(2)
    assert 20 < entropy_2 < 23  # ~22 bits

    entropy_3 = generator.get_entropy_bits(3)
    assert 32 < entropy_3 < 35  # ~33 bits


def test_case_insensitive():
    """Validation is case-insensitive"""
    generator = BIP39Generator()
    code = generator.generate_code(2)

    assert generator.validate_code(code.upper())
    assert generator.validate_code(code.lower())


def test_uniqueness():
    """Codes are statistically unique"""
    codes = [generate_code(2) for _ in range(100)]
    assert len(set(codes)) == 100  # All unique
