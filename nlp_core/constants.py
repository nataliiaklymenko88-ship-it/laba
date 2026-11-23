from __future__ import annotations

MIN_WORDS: int = 3
MAX_CHARS: int = 20_000
MIN_CYRILLIC_RATIO: float = 0.8
MIN_UK_MARKER_RATIO: float = 0.01
MIN_LETTERS_FOR_MARKER_CHECK: int = 50

UK_SPECIFIC_LETTERS: frozenset[str] = frozenset("іїєґ")
RU_SPECIFIC_LETTERS: frozenset[str] = frozenset("ыэъё")

UNKNOWN_POS: str = "UNKN"

POS_NAMES_UK: dict[str, str] = {
    "NOUN": "іменник",
    "ADJF": "прикметник",
    "ADJS": "прикметник (короткий)",
    "COMP": "компаратив",
    "VERB": "дієслово",
    "INFN": "інфінітив",
    "PRTF": "дієприкметник",
    "PRTS": "дієприкметник (короткий)",
    "GRND": "дієприслівник",
    "NUMR": "числівник",
    "ADVB": "прислівник",
    "NPRO": "займенник",
    "PRED": "предикатив",
    "PREP": "прийменник",
    "CONJ": "сполучник",
    "PRCL": "частка",
    "INTJ": "вигук",
}

GENDER_NAMES_UK: dict[str, str] = {
    "masc": "чоловічий",
    "femn": "жіночий",
    "neut": "середній",
}

NUMBER_NAMES_UK: dict[str, str] = {
    "sing": "однина",
    "plur": "множина",
}

CASE_NAMES_UK: dict[str, str] = {
    "nomn": "називний",
    "gent": "родовий",
    "gen2": "родовий",
    "datv": "давальний",
    "accs": "знахідний",
    "acc2": "знахідний",
    "ablt": "орудний",
    "loct": "місцевий",
    "loc2": "місцевий",
    "voct": "кличний",
}

POS_COLORS: dict[str, str] = {
    "NOUN": "#4f46e5",
    "ADJF": "#0891b2",
    "ADJS": "#0e7490",
    "COMP": "#0d9488",
    "VERB": "#dc2626",
    "INFN": "#b91c1c",
    "PRTF": "#ea580c",
    "PRTS": "#c2410c",
    "GRND": "#d97706",
    "NUMR": "#db2777",
    "ADVB": "#16a34a",
    "NPRO": "#9333ea",
    "PRED": "#65a30d",
    "PREP": "#64748b",
    "CONJ": "#475569",
    "PRCL": "#78716c",
    "INTJ": "#ca8a04",
}
DEFAULT_POS_COLOR: str = "#6b7280"
