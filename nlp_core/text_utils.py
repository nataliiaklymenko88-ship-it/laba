from __future__ import annotations

import re
from dataclasses import dataclass

from .constants import RU_SPECIFIC_LETTERS, UK_SPECIFIC_LETTERS

_LETTERS = "А-Яа-яІіЇїЄєҐґ"
_WORD_RE = re.compile(rf"[{_LETTERS}]+(?:['\-][{_LETTERS}]+)*")

_APOSTROPHE_TABLE = str.maketrans({"’": "'", "ʼ": "'", "`": "'"})

_ABBREVIATIONS: tuple[str, ...] = (
    "до н.е.", "т.д.", "т.п.", "т.ін.", "н.е.", "ст.", "див.", "напр.",
    "ім.", "вул.", "тис.", "млн.", "проф.", "доц.",
)
_ABBREVIATION_RE = re.compile(
    r"(?<!\S)(?:" + "|".join(re.escape(a) for a in _ABBREVIATIONS) + r")(?=\s)"
)
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?…])\s+(?=[«„\"(\dA-ZА-ЯІЇЄҐ])")
_DOT_PLACEHOLDER = "\x00"


@dataclass(frozen=True)
class LanguageStats:
    letters: int
    cyrillic: int
    uk_markers: int
    ru_markers: int

    @property
    def cyrillic_ratio(self) -> float:
        return self.cyrillic / self.letters if self.letters else 0.0

    @property
    def uk_marker_ratio(self) -> float:
        return self.uk_markers / self.cyrillic if self.cyrillic else 0.0


def normalize_text(text: str) -> str:
    text = text.translate(_APOSTROPHE_TABLE)
    return re.sub(r"[ \t]+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for line in text.splitlines():
        protected = _ABBREVIATION_RE.sub(
            lambda match: match.group(0).replace(".", _DOT_PLACEHOLDER), line
        )
        for chunk in _SENTENCE_BOUNDARY_RE.split(protected):
            restored = chunk.replace(_DOT_PLACEHOLDER, ".").strip()
            if restored:
                sentences.append(restored)
    return sentences


def tokenize_words(sentence: str) -> list[str]:
    return _WORD_RE.findall(sentence)


def compute_language_stats(text: str) -> LanguageStats:
    letters = [ch for ch in text.lower() if ch.isalpha()]
    cyrillic = [ch for ch in letters if "\u0400" <= ch <= "\u04FF"]
    return LanguageStats(
        letters=len(letters),
        cyrillic=len(cyrillic),
        uk_markers=sum(ch in UK_SPECIFIC_LETTERS for ch in cyrillic),
        ru_markers=sum(ch in RU_SPECIFIC_LETTERS for ch in cyrillic),
    )