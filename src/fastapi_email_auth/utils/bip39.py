"""BIP-39 mnemonic code generation utilities

Supports multiple languages for verification codes.
"""

import secrets
from typing import Literal

from mnemonic import Mnemonic

Language = Literal[
    "english",
    "russian",
    "chinese_simplified",
    "chinese_traditional",
    "french",
    "italian",
    "japanese",
    "korean",
    "spanish",
]


class BIP39Generator:
    """Generate verification codes using BIP-39 mnemonic words

    Supports multiple languages and configurable word counts.
    Uses cryptographically secure random number generator.
    """

    def __init__(self, language: Language = "english"):
        """Initialize generator with specified language

        Args:
            language: BIP-39 language (default: "english")

        Raises:
            ValueError: If language is not supported
        """
        try:
            self.mnemo = Mnemonic(language)
            self.language = language
        except Exception as e:
            raise ValueError(f"Unsupported language: {language}") from e

    def generate_code(self, word_count: int = 2, separator: str = " ") -> str:
        """Generate verification code from random BIP-39 words

        Args:
            word_count: Number of words (1-12, default: 2)
            separator: Word separator (default: space)

        Returns:
            Verification code like "солнце-река" or "abandon ability"

        Raises:
            ValueError: If word_count is out of valid range
        """
        if not 1 <= word_count <= 12:
            raise ValueError("word_count must be between 1 and 12")

        wordlist = self.mnemo.wordlist
        words = secrets.SystemRandom().sample(wordlist, word_count)
        return separator.join(words)

    def validate_code(self, code: str, separator: str = " ") -> bool:
        """Validate that code contains valid BIP-39 words

        Args:
            code: Code string to validate
            separator: Word separator used in code

        Returns:
            True if all words are valid BIP-39 words
        """
        words = code.lower().strip().split(separator)
        wordlist_lower = [w.lower() for w in self.mnemo.wordlist]
        return all(word in wordlist_lower for word in words)

    def get_entropy_bits(self, word_count: int) -> float:
        """Calculate entropy in bits for given word count

        Args:
            word_count: Number of words in code

        Returns:
            Entropy in bits (e.g., 2 words ≈ 22 bits)
        """
        import math

        combinations = len(self.mnemo.wordlist) ** word_count
        return math.log2(combinations)


# Convenience functions for common use cases
def generate_code(
    word_count: int = 2, language: Language = "english", separator: str = " "
) -> str:
    """Generate BIP-39 verification code

    Args:
        word_count: Number of words (default: 2)
        language: BIP-39 language (default: "english")
        separator: Word separator (default: space)

    Returns:
        Verification code string

    Examples:
        >>> generate_code(2, "english")
        'abandon ability'

        >>> generate_code(2, "russian", "-")
        'солнце-река'
    """
    generator = BIP39Generator(language)
    return generator.generate_code(word_count, separator)


def validate_code(
    code: str, language: Language = "english", separator: str = " "
) -> bool:
    """Validate BIP-39 code

    Args:
        code: Code to validate
        language: Expected language (default: "english")
        separator: Word separator (default: space)

    Returns:
        True if code is valid

    Examples:
        >>> validate_code("abandon ability", "english")
        True

        >>> validate_code("солнце-река", "russian", "-")
        True
    """
    generator = BIP39Generator(language)
    return generator.validate_code(code, separator)
