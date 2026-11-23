from __future__ import annotations

from collections import Counter
from functools import lru_cache

from .constants import CASE_NAMES_UK, GENDER_NAMES_UK, NUMBER_NAMES_UK, UNKNOWN_POS
from .models import NounProfile, Sentence, TextAnalysis, WordAnalysis
from .morphology import best_parse, is_indeclinable
from .rules import classify_declension, determine_group, is_abstract, is_collective
from .text_utils import normalize_text, split_sentences, tokenize_words


class NotNounError(ValueError):
    pass


@lru_cache(maxsize=100_000)
def analyze_word(surface: str) -> WordAnalysis:
    parse = best_parse(surface)
    tag = parse.tag
    lemma_parse = parse.normalized

    lemma = lemma_parse.word
    if surface[:1].isupper():
        lemma = lemma[:1].upper() + lemma[1:]

    is_noun = tag.POS == "NOUN"
    return WordAnalysis(
        surface=surface,
        lemma=lemma,
        pos=tag.POS or UNKNOWN_POS,
        gender=tag.gender,
        number=tag.number,
        case=tag.case,
        lemma_gender=lemma_parse.tag.gender,
        lemma_number=lemma_parse.tag.number,
        indeclinable=is_noun and is_indeclinable(parse),
        score=parse.score,
    )


def analyze_text(raw_text: str) -> TextAnalysis:
    text = normalize_text(raw_text)
    sentences: list[Sentence] = []
    for number, sentence_text in enumerate(split_sentences(text), start=1):
        words = tuple(analyze_word(token) for token in tokenize_words(sentence_text))
        sentences.append(Sentence(number=number, text=sentence_text, words=words))

    frequency = Counter(
        word.lemma.lower()
        for sentence in sentences
        for word in sentence.words
        if word.pos == "NOUN"
    )
    return TextAnalysis(sentences=tuple(sentences), noun_frequency=frequency)


def get_sentence(analysis: TextAnalysis, number: int) -> Sentence:
    return analysis.sentences[number - 1]


def iter_nouns(analysis: TextAnalysis) -> list[tuple[int, WordAnalysis]]:
    return [
        (sentence.number, word)
        for sentence in analysis.sentences
        for word in sentence.words
        if word.pos == "NOUN"
    ]


def noun_frequency_table(analysis: TextAnalysis) -> list[tuple[str, int]]:
    return sorted(analysis.noun_frequency.items(), key=lambda item: (-item[1], item[0]))


def describe_noun(word: WordAnalysis) -> NounProfile:
    if word.pos != "NOUN":
        raise NotNounError(f"Слово «{word.surface}» не є іменником.")

    lemma = word.lemma.lower()
    declension = classify_declension(
        lemma, word.lemma_gender, word.lemma_number, word.indeclinable
    )
    return NounProfile(
        surface=word.surface,
        lemma=word.lemma,
        gender=word.lemma_gender,
        number=word.number,
        case=word.case,
        declension=declension,
        group=determine_group(lemma, declension),
        is_abstract=is_abstract(lemma),
        is_collective=is_collective(lemma),
        is_indeclinable=word.indeclinable,
    )


def _label(mapping: dict[str, str], key: str | None) -> str:
    return mapping.get(key, "—") if key else "—"


def _yes_no(value: bool) -> str:
    return "так" if value else "ні"


def profile_to_rows(profile: NounProfile) -> list[tuple[str, str]]:
    return [
        ("Словоформа", profile.surface),
        ("Початкова форма", profile.lemma),
        ("Рід (за початковою формою)", _label(GENDER_NAMES_UK, profile.gender)),
        ("Число у тексті", _label(NUMBER_NAMES_UK, profile.number)),
        ("Відмінок у тексті", _label(CASE_NAMES_UK, profile.case)),
        ("Відміна", profile.declension),
        ("Група", profile.group or "—"),
        ("Абстрактний", _yes_no(profile.is_abstract)),
        ("Збірний", _yes_no(profile.is_collective)),
        ("Невідмінюваний", _yes_no(profile.is_indeclinable)),
    ]