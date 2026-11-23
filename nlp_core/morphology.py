from __future__ import annotations

from functools import lru_cache

import pymorphy3
from pymorphy3.analyzer import Parse


@lru_cache(maxsize=1)
def get_analyzer() -> pymorphy3.MorphAnalyzer:
    return pymorphy3.MorphAnalyzer(lang="uk")


@lru_cache(maxsize=100_000)
def best_parse(word: str) -> Parse:
    parses = get_analyzer().parse(word.lower())
    return max(parses, key=lambda parse: parse.score)


def is_indeclinable(parse: Parse) -> bool:
    forms = {form.word for form in parse.lexeme}
    return len(parse.lexeme) > 1 and len(forms) == 1