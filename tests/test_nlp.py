from pathlib import Path

import pytest

from nlp_core import (
    InputValidationError,
    NotNounError,
    analyze_text,
    analyze_word,
    describe_noun,
    get_sentence,
    iter_nouns,
    noun_frequency_table,
    parse_sentence_number,
    split_sentences,
    tokenize_words,
    validate_text,
)
from nlp_core.constants import MAX_CHARS
from nlp_core.rules import (
    DECLENSION_I,
    DECLENSION_II,
    DECLENSION_III,
    DECLENSION_UNDEFINED,
    GROUP_HARD,
    GROUP_SOFT,
    classify_declension,
    determine_group,
    is_abstract,
    is_collective,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE_FILES = ["fiction.txt", "publicistic.txt", "official.txt"]


@pytest.mark.parametrize("text", ["", "   ", "\n\t  "])
def test_empty_input_is_rejected(text: str) -> None:
    report = validate_text(text)
    assert not report.is_valid
    assert "порожній" in report.errors[0]


def test_digits_only_is_rejected() -> None:
    report = validate_text("12345 67890 !!!")
    assert not report.is_valid
    assert "немає літер" in report.errors[0]


def test_latin_text_is_rejected() -> None:
    report = validate_text("This is an English sentence for testing purposes.")
    assert not report.is_valid
    assert "українською" in report.errors[0]


def test_non_ukrainian_latin_text_is_rejected_for_long_input() -> None:
    text = "The old house stood by the river and the children played near the water every single summer afternoon."
    report = validate_text(text)
    assert not report.is_valid


def test_too_short_text_is_rejected() -> None:
    report = validate_text("Вода тече.")
    assert not report.is_valid
    assert "занадто короткий" in report.errors[0]


def test_too_long_text_is_rejected() -> None:
    text = "слово " * (MAX_CHARS // 5 + 100)
    report = validate_text(text)
    assert not report.is_valid
    assert "занадто довгий" in report.errors[0]


def test_russian_marker_gives_warning_not_error() -> None:
    report = validate_text("Це ё текст для перевірки мови.")
    assert report.is_valid
    assert report.warnings


def test_valid_ukrainian_text_passes() -> None:
    report = validate_text("Ранок над селом був тихим і прохолодним.")
    assert report.is_valid
    assert not report.errors


def test_split_sentences_basic() -> None:
    assert len(split_sentences("Перше речення. Друге речення! Третє?")) == 3


def test_split_sentences_protects_abbreviations() -> None:
    sentences = split_sentences("Це зроблено, напр. для тесту. Далі йде інше речення.")
    assert len(sentences) == 2


def test_split_sentences_keeps_abbreviation_in_one_sentence() -> None:
    sentences = split_sentences("Відповідно до ст. 79 Кодексу законів про працю України працівник має право.")
    assert len(sentences) == 1


def test_tokenize_keeps_apostrophe_and_hyphen() -> None:
    assert tokenize_words("м'ясо та кіт-кіт!") == ["м'ясо", "та", "кіт-кіт"]


@pytest.mark.parametrize(
    ("raw", "total", "expected"),
    [("1", 3, 1), ("3", 3, 3), (" 2 ", 3, 2)],
)
def test_sentence_number_valid(raw: str, total: int, expected: int) -> None:
    assert parse_sentence_number(raw, total) == expected


@pytest.mark.parametrize(
    ("raw", "total"),
    [("0", 3), ("4", 3), ("-1", 3), ("abc", 3), ("", 3), ("1", 0)],
)
def test_sentence_number_invalid(raw: str, total: int) -> None:
    with pytest.raises(InputValidationError):
        parse_sentence_number(raw, total)


@pytest.mark.parametrize(
    ("lemma", "gender", "number", "expected"),
    [
        ("вода", "femn", "sing", DECLENSION_I),
        ("земля", "femn", "sing", DECLENSION_I),
        ("суддя", "masc", "sing", DECLENSION_I),
        ("ніч", "femn", "sing", DECLENSION_III),
        ("радість", "femn", "sing", DECLENSION_III),
        ("стіл", "masc", "sing", DECLENSION_II),
        ("кінь", "masc", "sing", DECLENSION_II),
        ("вікно", "neut", "sing", DECLENSION_II),
        ("поле", "neut", "sing", DECLENSION_II),
        ("ім'я", "neut", "sing", DECLENSION_III),
        ("ворота", "neut", "plur", DECLENSION_UNDEFINED),
    ],
)
def test_declension(lemma: str, gender: str, number: str, expected: str) -> None:
    assert classify_declension(lemma, gender, number, indeclinable=False) == expected


def test_indeclinable_has_no_declension() -> None:
    assert classify_declension("кіно", "neut", "sing", indeclinable=True) == "невідмінюваний"


@pytest.mark.parametrize(
    ("lemma", "declension", "expected"),
    [
        ("вода", DECLENSION_I, GROUP_HARD),
        ("земля", DECLENSION_I, GROUP_SOFT),
        ("стіл", DECLENSION_II, GROUP_HARD),
        ("вікно", DECLENSION_II, GROUP_HARD),
        ("кінь", DECLENSION_II, GROUP_SOFT),
        ("край", DECLENSION_II, GROUP_SOFT),
        ("поле", DECLENSION_II, GROUP_SOFT),
        ("життя", DECLENSION_II, GROUP_SOFT),
        ("ніч", DECLENSION_III, None),
    ],
)
def test_group(lemma: str, declension: str, expected: str | None) -> None:
    assert determine_group(lemma, declension) == expected


@pytest.mark.parametrize("lemma", ["радість", "читання", "братство", "доброта", "рішення"])
def test_abstract_nouns(lemma: str) -> None:
    assert is_abstract(lemma)


@pytest.mark.parametrize("lemma", ["стіл", "вода", "кіт"])
def test_concrete_nouns_are_not_abstract(lemma: str) -> None:
    assert not is_abstract(lemma)


@pytest.mark.parametrize("lemma", ["листя", "військо", "молодь"])
def test_collective_nouns(lemma: str) -> None:
    assert is_collective(lemma)


def test_non_collective_noun() -> None:
    assert not is_collective("стіл")


def test_analyze_word_noun() -> None:
    word = analyze_word("вода")
    assert word.pos == "NOUN"
    assert word.lemma == "вода"


def test_analyze_word_inflected_noun_gets_lemma() -> None:
    assert analyze_word("столом").lemma == "стіл"


def test_describe_noun_feminine_first_declension() -> None:
    profile = describe_noun(analyze_word("вода"))
    assert profile.lemma == "вода"
    assert profile.gender == "femn"
    assert profile.declension == DECLENSION_I
    assert profile.group == GROUP_HARD
    assert not profile.is_abstract


def test_describe_noun_abstract_third_declension() -> None:
    profile = describe_noun(analyze_word("радість"))
    assert profile.declension == DECLENSION_III
    assert profile.group is None
    assert profile.is_abstract


def test_describe_noun_rejects_verb() -> None:
    with pytest.raises(NotNounError):
        describe_noun(analyze_word("читає"))


def test_analyze_text_numbers_sentences_from_one() -> None:
    analysis = analyze_text("Вода тече. Вода холодна.")
    assert [sentence.number for sentence in analysis.sentences] == [1, 2]
    assert get_sentence(analysis, 2).number == 2


def test_noun_frequency_counts_lemmas_case_insensitively() -> None:
    analysis = analyze_text("Вода тече. Вода холодна.")
    assert analysis.noun_frequency["вода"] == 2
    assert noun_frequency_table(analysis)[0] == ("вода", 2)


def test_iter_nouns_returns_sentence_numbers() -> None:
    analysis = analyze_text("Вода тече. Вода холодна.")
    nouns = iter_nouns(analysis)
    assert nouns
    assert all(number in (1, 2) for number, _ in nouns)


@pytest.mark.parametrize("name", SAMPLE_FILES)
def test_sample_texts_are_valid_and_contain_nouns(name: str) -> None:
    text = (DATA_DIR / name).read_text(encoding="utf-8")
    assert validate_text(text).is_valid
    analysis = analyze_text(text)
    assert len(analysis.sentences) >= 5
    assert iter_nouns(analysis)