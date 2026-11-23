from __future__ import annotations

from dataclasses import dataclass

from .constants import (
    MAX_CHARS,
    MIN_CYRILLIC_RATIO,
    MIN_LETTERS_FOR_MARKER_CHECK,
    MIN_UK_MARKER_RATIO,
    MIN_WORDS,
)
from .text_utils import compute_language_stats, normalize_text, tokenize_words


class InputValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_text(raw_text: str) -> ValidationReport:
    if not raw_text or not raw_text.strip():
        return ValidationReport(
            errors=("Текст порожній. Вставте речення українською мовою або оберіть тестовий текст.",)
        )

    text = normalize_text(raw_text)
    stats = compute_language_stats(text)
    if stats.letters == 0:
        return ValidationReport(
            errors=("У тексті немає літер. Введіть речення українською мовою, а не лише цифри чи символи.",)
        )

    errors: list[str] = []
    warnings: list[str] = []

    if len(text) > MAX_CHARS:
        errors.append(f"Текст занадто довгий: {len(text)} символів. Ліміт — {MAX_CHARS} символів.")
    if len(tokenize_words(text)) < MIN_WORDS:
        errors.append(f"Текст занадто короткий: потрібно щонайменше {MIN_WORDS} слова.")

    not_ukrainian = stats.cyrillic_ratio < MIN_CYRILLIC_RATIO or (
        stats.letters >= MIN_LETTERS_FOR_MARKER_CHECK
        and stats.uk_marker_ratio < MIN_UK_MARKER_RATIO
    )
    if not_ukrainian:
        errors.append("Текст має бути переважно українською мовою. Виявлено латиницю або іншу мову.")
    elif stats.ru_markers:
        warnings.append(
            "Знайдено літери ё, ы, э, ъ, характерні для російської мови. "
            "Перевірте, чи текст українською."
        )

    return ValidationReport(errors=tuple(errors), warnings=tuple(warnings))


def parse_sentence_number(raw: str, total_sentences: int) -> int:
    value = raw.strip()
    if not value.isdigit():
        raise InputValidationError("Номер речення має бути цілим додатним числом.")
    if total_sentences == 0:
        raise InputValidationError("У тексті немає речень для вибору.")
    number = int(value)
    if not 1 <= number <= total_sentences:
        raise InputValidationError(
            f"Речення з номером {number} немає. У тексті речень: {total_sentences}."
        )
    return number