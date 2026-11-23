from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from nlp_core import (
    InputValidationError,
    NotNounError,
    TextAnalysis,
    analyze_text,
    describe_noun,
    get_sentence,
    iter_nouns,
    noun_frequency_table,
    parse_sentence_number,
    profile_to_rows,
    validate_text,
)
from nlp_core.models import Sentence

DATA_DIR = Path(__file__).parent / "data"
SAMPLES: dict[str, str] = {
    "Художній текст": "fiction.txt",
    "Науково-публіцистичний текст": "publicistic.txt",
    "Офіційно-діловий текст": "official.txt",
}
TOKEN_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]+(?:['\-][А-Яа-яІіЇїЄєҐґ]+)*")

CSS = """
<style>
.hero {background: linear-gradient(135deg, #4f46e5, #0891b2); color: #ffffff; padding: 22px 26px; border-radius: 16px; margin-bottom: 18px;}
.hero h2 {margin: 0 0 6px 0; color: #ffffff;}
.hero p {margin: 0; opacity: 0.92;}
.sentence {background: #f8fafc; border-left: 4px solid #4f46e5; padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; line-height: 1.9; font-size: 1.05rem; color: #0f172a;}
.sentence-num {display: inline-block; min-width: 28px; font-weight: 700; color: #4f46e5;}
.badge-noun {background: #4f46e5; color: #ffffff; border-radius: 6px; padding: 1px 6px; font-weight: 600;}
.legend {color: #334155; margin: 4px 0 14px 0;}
.card-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 8px;}
.card {background: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);}
.card .label {color: #64748b; font-size: 0.85rem; margin-bottom: 4px;}
.card .value {font-weight: 600; font-size: 1.05rem;}
</style>
"""

RULES_TEXT = """
### Як визначаються ознаки іменника

- **Морфологія.** Словоформи розбирає бібліотека pymorphy3 зі словником української мови. Для слова обирається розбір із найбільшим показником ймовірності (score). Контекстного зняття омонімії немає, тому омоніми визначаються частотністю розбору.
- **Рід.** Визначається за початковою формою (лемою), бо у множині роду немає. Слово «води» отримує рід леми «вода», тобто жіночий.
- **Число, відмінок.** Беруться з граматичних тегів словоформи у тексті.
- **Відміна.** I відміна: жіночий рід на -а, -я, а також чоловічий на -а, -я (Микита, суддя). II відміна: чоловічий на приголосний чи -ь, -й, -о, а також середній на -о, -е, -я. III відміна: жіночий на -ь і інші жіночі, а також середній на -мя (ім'я).
- **Група.** Лише для I та II відмін. I відміна: -я (земля) — м'яка, решта — тверда. II відміна: -ь, -й, -е, -я (кінь, край, поле, життя) — м'яка, решта (стіл, вікно) — тверда.
- **Абстрактність.** За суфіксами леми: -ість, -ство, -ння, -ття, -ота, -изм/-ізм, -ація (радість, братство, читання).
- **Збірність.** За словником збірних іменників (листя, військо, молодь), бо за формою слова це надійно не виводиться.
- **Невідмінюваність.** Іменник має кілька граматичних форм, які записуються однаково (кіно, таксі). Для нього відміна не визначається.

### Обмеження

Омонімія вирішується лише за частотністю розбору. Абстрактність за суфіксами не покриває всіх слів (наприклад, «дружба»). Збірність покривається лише словником. Правила навмисно спрощені до шкільної класифікації.
"""


def load_sample(filename: str) -> str:
    return (DATA_DIR / filename).read_text(encoding="utf-8").strip()


def set_sample(filename: str) -> None:
    st.session_state["input_text"] = load_sample(filename)


def run_analysis(text: str) -> None:
    report = validate_text(text)
    st.session_state["warnings"] = list(report.warnings)
    st.session_state["errors"] = list(report.errors)
    if not report.is_valid:
        st.session_state["analysis"] = None
        return
    st.session_state["analysis"] = analyze_text(text)


def highlight_sentence(sentence: Sentence) -> str:
    parts: list[str] = []
    cursor = 0
    for match, word in zip(TOKEN_RE.finditer(sentence.text), sentence.words):
        parts.append(html.escape(sentence.text[cursor:match.start()]))
        token = html.escape(match.group())
        if word.pos == "NOUN":
            parts.append(
                f'<span class="badge-noun" title="Початкова форма: {html.escape(word.lemma)}">{token}</span>'
            )
        else:
            parts.append(token)
        cursor = match.end()
    parts.append(html.escape(sentence.text[cursor:]))
    return "".join(parts)


def noun_frame(analysis: TextAnalysis) -> pd.DataFrame:
    rows = [
        {"Речення": number, "Словоформа": word.surface, "Початкова форма": word.lemma}
        for number, word in iter_nouns(analysis)
    ]
    return pd.DataFrame(rows, columns=["Речення", "Словоформа", "Початкова форма"])


def frequency_frame(analysis: TextAnalysis) -> pd.DataFrame:
    rows = [
        {"Початкова форма": lemma, "Кількість": count}
        for lemma, count in noun_frequency_table(analysis)
    ]
    return pd.DataFrame(rows, columns=["Початкова форма", "Кількість"])


def render_cards(rows: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="card"><div class="label">{html.escape(label)}</div>'
        f'<div class="value">{html.escape(value)}</div></div>'
        for label, value in rows
    )
    st.markdown(f'<div class="card-grid">{cards}</div>', unsafe_allow_html=True)


def render_input_section() -> None:
    st.session_state.setdefault("input_text", "")

    st.markdown("**Завантажте один із тестових текстів для швидкої демонстрації:**")
    columns = st.columns(len(SAMPLES))
    for column, (title, filename) in zip(columns, SAMPLES.items()):
        column.button(title, on_click=set_sample, args=(filename,), key=f"sample_{filename}")

    st.caption(
        "Формат: український текст від 3 слів до 20 000 символів. "
        "Речення відокремлюйте крапкою, знаком оклику або знаком питання."
    )
    st.text_area(
        "Текст українською мовою",
        key="input_text",
        height=220,
        placeholder="Наприклад: Ранок над селом був тихим і прохолодним. Старий дід вийшов із хати.",
    )

    if st.button("Аналізувати текст", type="primary"):
        run_analysis(st.session_state["input_text"])


def render_text_tab(analysis: TextAnalysis) -> None:
    st.markdown(
        '<div class="legend"><span class="badge-noun">іменник</span> '
        "наведіть курсор на виділене слово, щоб побачити його початкову форму</div>",
        unsafe_allow_html=True,
    )
    for sentence in analysis.sentences:
        st.markdown(
            f'<div class="sentence"><span class="sentence-num">{sentence.number}.</span> '
            f"{highlight_sentence(sentence)}</div>",
            unsafe_allow_html=True,
        )


def render_nouns_tab(analysis: TextAnalysis) -> None:
    nouns = noun_frame(analysis)
    if nouns.empty:
        st.info("У тексті не знайдено іменників.")
        return
    st.dataframe(nouns, hide_index=True)

    st.subheader("Іменники обраного речення")
    raw_number = st.text_input(
        f"Номер речення (від 1 до {len(analysis.sentences)})",
        key="sentence_number",
        placeholder="Наприклад, 1",
    )
    if not raw_number.strip():
        st.info("Введіть номер речення, щоб побачити його іменники.")
        return
    try:
        number = parse_sentence_number(raw_number, len(analysis.sentences))
    except InputValidationError as error:
        st.error(str(error))
        return

    sentence = get_sentence(analysis, number)
    st.markdown(
        f'<div class="sentence"><span class="sentence-num">{sentence.number}.</span> '
        f"{highlight_sentence(sentence)}</div>",
        unsafe_allow_html=True,
    )
    sentence_nouns = [word for word in sentence.words if word.pos == "NOUN"]
    if sentence_nouns:
        pairs = ", ".join(
            f"{html.escape(word.surface)} → {html.escape(word.lemma)}" for word in sentence_nouns
        )
        st.markdown(f"**Іменники у реченні {number}:** {pairs}", unsafe_allow_html=True)
    else:
        st.info(f"У реченні {number} іменників немає.")


def render_frequency_tab(analysis: TextAnalysis) -> None:
    frequency = frequency_frame(analysis)
    if frequency.empty:
        st.info("Немає іменників для підрахунку частотності.")
        return
    left, right = st.columns([2, 3])
    with left:
        st.dataframe(frequency, hide_index=True)
    with right:
        st.bar_chart(frequency.head(10), x="Початкова форма", y="Кількість")


def render_profile_tab(analysis: TextAnalysis) -> None:
    nouns = iter_nouns(analysis)
    if not nouns:
        st.info("У тексті не знайдено іменників для розбору.")
        return

    index = st.selectbox(
        "Оберіть іменник для морфологічного розбору",
        options=range(len(nouns)),
        format_func=lambda i: f"{nouns[i][1].surface} (речення {nouns[i][0]}, позиція {i + 1})",
    )
    _, word = nouns[index]
    try:
        profile = describe_noun(word)
    except NotNounError as error:
        st.error(str(error))
        return
    render_cards(profile_to_rows(profile))


def render_rules_tab() -> None:
    st.markdown(RULES_TEXT)


def main() -> None:
    st.set_page_config(page_title="Іменники в українському тексті", page_icon="📝", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero"><h2>Іменники в українському тексті</h2>'
        "<p>Пошук і підсвітка іменників, їхня частотність та морфологічний розбір: "
        "рід, число, відмінок, відміна, група, абстрактність і збірність.</p></div>",
        unsafe_allow_html=True,
    )

    render_input_section()

    for message in st.session_state.get("warnings", []):
        st.warning(message)
    for message in st.session_state.get("errors", []):
        st.error(message)

    analysis: TextAnalysis | None = st.session_state.get("analysis")
    if analysis is None:
        st.info("Введіть текст або оберіть тестовий і натисніть «Аналізувати текст».")
        return

    total_nouns = len(iter_nouns(analysis))
    first, second, third = st.columns(3)
    first.metric("Речень", len(analysis.sentences))
    second.metric("Іменників", total_nouns)
    third.metric("Різних лем-іменників", len(analysis.noun_frequency))

    tab_text, tab_nouns, tab_frequency, tab_profile, tab_rules = st.tabs(
        ["Підсвітка тексту", "Іменники", "Частотність", "Морфологічний розбір", "Правила"]
    )
    with tab_text:
        render_text_tab(analysis)
    with tab_nouns:
        render_nouns_tab(analysis)
    with tab_frequency:
        render_frequency_tab(analysis)
    with tab_profile:
        render_profile_tab(analysis)
    with tab_rules:
        render_rules_tab()


main()