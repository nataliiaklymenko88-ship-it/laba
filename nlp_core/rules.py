from __future__ import annotations

DECLENSION_I = "I відміна"
DECLENSION_II = "II відміна"
DECLENSION_III = "III відміна"
DECLENSION_INDECLINABLE = "невідмінюваний"
DECLENSION_UNDEFINED = "не визначено"

GROUP_HARD = "тверда група"
GROUP_SOFT = "м'яка група"

ABSTRACT_SUFFIXES: tuple[str, ...] = (
    "ість", "ство", "ння", "ття", "ота", "изм", "ізм", "ація",
)

COLLECTIVE_NOUNS: frozenset[str] = frozenset({
    "листя", "гілля", "каміння", "коріння", "військо", "молодь",
    "дітвора", "духовенство", "студентство", "козацтво", "людство",
})


def classify_declension(
    lemma: str,
    lemma_gender: str | None,
    lemma_number: str | None,
    indeclinable: bool,
) -> str:
    lemma = lemma.lower()
    if indeclinable:
        return DECLENSION_INDECLINABLE
    if lemma_number == "plur" or lemma_gender is None:
        return DECLENSION_UNDEFINED
    if lemma_gender == "femn":
        return DECLENSION_I if lemma.endswith(("а", "я")) else DECLENSION_III
    if lemma_gender == "neut":
        return DECLENSION_III if lemma.endswith(("мя", "м'я")) else DECLENSION_II
    return DECLENSION_I if lemma.endswith(("а", "я")) else DECLENSION_II


def determine_group(lemma: str, declension: str) -> str | None:
    lemma = lemma.lower()
    if declension == DECLENSION_I:
        return GROUP_SOFT if lemma.endswith("я") else GROUP_HARD
    if declension == DECLENSION_II:
        return GROUP_SOFT if lemma.endswith(("ь", "й", "е", "я")) else GROUP_HARD
    return None


def is_abstract(lemma: str) -> bool:
    return lemma.lower().endswith(ABSTRACT_SUFFIXES)


def is_collective(lemma: str) -> bool:
    return lemma.lower() in COLLECTIVE_NOUNS