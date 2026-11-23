from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class WordAnalysis:
    surface: str
    lemma: str
    pos: str
    gender: str | None
    number: str | None
    case: str | None
    lemma_gender: str | None
    lemma_number: str | None
    indeclinable: bool
    score: float


@dataclass(frozen=True)
class Sentence:
    number: int
    text: str
    words: tuple[WordAnalysis, ...]


@dataclass(frozen=True)
class TextAnalysis:
    sentences: tuple[Sentence, ...]
    noun_frequency: Counter[str]


@dataclass(frozen=True)
class NounProfile:
    surface: str
    lemma: str
    gender: str | None
    number: str | None
    case: str | None
    declension: str
    group: str | None
    is_abstract: bool
    is_collective: bool
    is_indeclinable: bool