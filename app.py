import itertools
import json
from pathlib import Path
from html import escape

import streamlit as st


# =========================================================
# 1. PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Number Possibility Pyramid",
    page_icon="🔺",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# 2. EXACT DIGIT MAPPING
# =========================================================

MAPPING = {
    "0": ["3", "9"],
    "1": ["8", "4"],
    "2": ["3", "6"],
    "3": ["4", "8"],
    "4": ["6", "3"],
    "5": ["0", "7"],
    "6": ["2", "1"],
    "7": ["4", "5"],
    "8": ["6", "2"],
    "9": ["2", "0"],
}


# =========================================================
# 3. PERSISTENT ROTATION STATE
# =========================================================

STATE_FILE = Path(__file__).with_name("rotation_state.json")

DEFAULT_STATE = {
    "last_input": "546",
    "rotation_index": 0,
}


def load_state():
    """Load the saved input and rotation position."""
    try:
        if STATE_FILE.exists():
            with STATE_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)

            number = data.get("last_input", "546")
            index = data.get("rotation_index", 0)

            if (
                isinstance(number, str)
                and number.isdigit()
                and 3 <= len(number) <= 6
                and isinstance(index, int)
                and not isinstance(index, bool)
                and index >= 0
            ):
                return {
                    "last_input": number,
                    "rotation_index": index,
                }

    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass

    return DEFAULT_STATE.copy()


def save_state(state):
    """Save the rotation state for later reruns and refreshes."""
    temporary_file = STATE_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)

    temporary_file.replace(STATE_FILE)


# =========================================================
# 4. GENERATE VALID COMBINATIONS
# =========================================================

def generate_combinations(number):
    """
    Generate combinations from the exact mapping.
    """
    if not isinstance(number, str):
        return []

    if not number.isdigit() or not 3 <= len(number) <= 6:
        return []

    choices = [MAPPING[digit] for digit in number]

    combinations = (
        "".join(digits)
        for digits in itertools.product(*choices)
    )

    return list(dict.fromkeys(combinations))


def get_possibilities(number, rotation_index):
    """Return two fixed possibilities and one rotating possibility."""
    combinations = generate_combinations(number)

    fixed_one = combinations[0] if len(combinations) >= 1 else None
    fixed_two = combinations[1] if len(combinations) >= 2 else None

    rotating_combinations = combinations[2:]

    if rotating_combinations:
        rotating = rotating_combinations[
            rotation_index % len(rotating_combinations)
        ]
    else:
        rotating = None

    return fixed_one, fixed_two, rotating, len(rotating_combinations)


# =========================================================
# 5. CUSTOM DARK NEON DESIGN
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at 50% 0%,
                #101a49 0%, #050b20 42%, #020615 100%);
        color: #e8f1ff;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .main-title {
        text-align: center;
        font-size: clamp(2rem, 4vw, 3.2rem);
        font-weight: 900;
        letter-spacing: -1px;
        background: linear-gradient(
            90deg, #18d9ff, #6687ff, #db73ff
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        color: #9cbcff;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    [data-testid="stForm"] {
        background: rgba(4, 19, 49, 0.88);
        border: 1px solid #154ba0;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 0 22px rgba(0, 100, 255, 0.10);
    }

    [data-testid="stTextInput"] label {
        color: #a9caff !important;
        font-weight: 700;
    }

    [data-testid="stTextInput"] input {
        background: #071735 !important;
        color: #ffffff !important;
        border: 1px solid #285bd0 !important;
        border-radius: 10px !important;
        font-size: 1.2rem !important;
    }

    .stButton > button,
    [data-testid="stFormSubmitButton"] button {
        min-height: 48px;
        width: 100%;
        color: white !important;
        font-weight: 800 !important;
        border: 0 !important;
        border-radius: 12px !important;
        background: linear-gradient(100deg, #079cff, #7735ff) !important;
        box-shadow: 0 0 22px rgba(64, 95, 255, 0.28);
    }

    .panel {
        background: rgba(4, 15, 37, 0.90);
        border: 1px solid #124c9e;
        border-radius: 20px;
        padding: 22px;
        min-height: 100%;
    }

    .panel-title {
        color: #78baff;
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 3px;
    }

    .panel-subtitle {
        color: #8eb6ff;
        font-size: 0.95rem;
        margin-bottom: 24px;
    }

    .pyramid {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 9px;
        padding: 8px 0 24px;
        width: 100%;
    }

    .pyramid-row {
        display: flex;
        justify-content: center;
        gap: 8px;
        width: 100%;
    }

    .digit-box {
        display: flex;
        align-items: center;
        justify-content: center;
        width: clamp(43px, 7vw, 66px);
        height: clamp(43px, 7vw, 66px);
        flex: 0 0 auto;
        border: 2px solid var(--digit-color);
        border-radius: 12px;
        color: #ffffff;
        background: var(--digit-bg);
        box-shadow: 0 0 13px var(--digit-glow),
                    inset 0 0 12px var(--digit-glow);
        font-size: clamp(1.2rem, 3vw, 1.9rem);
        font-weight: 900;
        text-shadow: 0 0 9px var(--digit-color);
    }

    .note {
        background: #061a3d;
        border: 1px solid #164a98;
        border-radius: 12px;
        padding: 13px;
        color: #b7d4ff;
        font-size: 0.9rem;
        margin-top: 10px;
    }

    .result-card {
        border: 2px solid var(--card-border);
        background: var(--card-bg);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 0 15px var(--card-glow);
    }

    .result-label {
        font-size: 0.98rem;
        font-weight: 900;
        color: var(--card-accent);
        margin-bottom: 8px;
    }

    .result-number {
        color: #f2f7ff;
        font-size: clamp(2rem, 4vw, 2.7rem);
        font-weight: 900;
        letter-spacing: 3px;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }

    .result-description {
        color: #a9caff;
        font-size: 0.88rem;
        margin-top: 8px;
    }

    .footer-note {
        text-align: center;
        color: #82a8e9;
        border-top: 1px solid #12366c;
        margin-top: 24px;
        padding-top: 16px;
        font-size: 0.84rem;
    }

    @media (max-width: 600px) {
        .panel {
            padding: 14px;
        }

        .digit-box {
            border-radius: 8px;
        }

        .result-card {
            padding: 16px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 6. TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🔺 Number Possibility Pyramid</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Enter a number (3 to 6 digits) to discover your possibilities'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# 7. INPUT AND GENERATE BUTTON
# =========================================================

state = load_state()
default_number = state["last_input"]

with st.form("number_form"):
    input_column, button_column = st.columns([4, 1.25])

    with input_column:
        entered_number = st.text_input(
            "Enter Number (3–6 digits)",
            value=default_number,
            max_chars=6,
            placeholder="Example: 546",
        )

    with button_column:
        st.markdown("<div style='height: 26px'></div>", unsafe_allow_html=True)
        generate_clicked = st.form_submit_button(
            "⚡ Generate",
            use_container_width=True,
        )


# =========================================================
# 8. VALIDATE INPUT AND UPDATE ROTATION
# =========================================================

valid_input = (
    entered_number.isdigit()
    and len(entered_number) in (3, 4, 5, 6)
)

if generate_clicked:
    if not valid_input:
        st.error("Please enter exactly 3, 4, 5, or 6 digits.")
    else:
        if entered_number != state["last_input"]:
            state = {
                "last_input": entered_number,
                "rotation_index": 0,
            }
        else:
            _, _, _, rotating_count = get_possibilities(
                entered_number,
                state["rotation_index"],
            )

            if rotating_count > 0:
                state["rotation_index"] = (
                    state["rotation_index"] + 1
                ) % rotating_count

        try:
            save_state(state)
        except OSError:
            st.warning(
                "Could not save rotation state. "
                "Check that the project folder is writable."
            )

elif valid_input and entered_number != state["last_input"]:
    pass


if generate_clicked and not valid_input:
    current_number = state["last_input"]
else:
    current_number = entered_number if valid_input else state["last_input"]


# =========================================================
# 9. CALCULATE EXACTLY THREE POSSIBILITIES
# =========================================================

fixed_one, fixed_two, rotating, rotating_count = get_possibilities(
    current_number,
    state["rotation_index"]
)


# =========================================================
# 10. PYRAMID BUILT FROM POSSIBILITY 1 (Forced 5-Row Structure)
# =========================================================

def make_pyramid(number):
    """
    Display each digit once in a centered pyramid.
    Automatically expands any 3, 4, 5, or 6-digit input 
    to fill a complete 5-row pyramid (15 digits total: 1+2+3+4+5).
    """
    if not number:
        return '<div class="note">No possibility available.</div>'

    # Expand the input digits using mapping/cycling until we reach 15 digits for 5 rows
    expanded_digits = list(number)
    i = 0
    while len(expanded_digits) < 15:
        current_digit = expanded_digits[i % len(expanded_digits)]
        if current_digit in MAPPING:
            expanded_digits.extend(MAPPING[current_digit])
        else:
            expanded_digits.append(current_digit)
        i += 1

    number = "".join(expanded_digits[:15])

    palette = [
        ("#16cfff", "rgba(0, 139, 255, 0.28)", "rgba(0, 180, 255, 0.38)"),
        ("#13e9c0", "rgba(0, 185, 145, 0.28)", "rgba(0, 255, 205, 0.36)"),
        ("#9b69ff", "rgba(103, 35, 255, 0.32)", "rgba(147, 70, 255, 0.40)"),
        ("#ff4b9b", "rgba(224, 20, 113, 0.30)", "rgba(255, 42, 145, 0.40)"),
        ("#ffb51b", "rgba(221, 111, 0, 0.30)", "rgba(255, 159, 0, 0.40)"),
        ("#28f47c", "rgba(0, 174, 70, 0.30)", "rgba(0, 255, 100, 0.38)"),
        ("#477bff", "rgba(0, 74, 235, 0.30)", "rgba(38, 105, 255, 0.40)"),
    ]

    rows_html = []
    position = 0
    row_size = 1

    while position < len(number):
        row_digits = number[position:position + row_size]
        boxes = []

        for digit in row_digits:
            color, background, glow = palette[position % len(palette)]

            boxes.append(
                '<div class="digit-box" '
                f'style="--digit-color:{color};'
                f'--digit-bg:{background};'
                f'--digit-glow:{glow};">'
                f'{escape(digit)}'
                '</div>'
            )
            position += 1

        rows_html.append(
            '<div class="pyramid-row">'
            + "".join(boxes)
            + '</div>'
        )

        row_size += 1

    return '<div class="pyramid">' + "".join(rows_html) + '</div>'


# =========================================================
# 11. RESULT CARD
# =========================================================

def result_card(label, number, description, accent, background, glow):
    display_number = number if number is not None else "Unavailable"

    return f"""
    <div class="result-card"
         style="--card-border:{accent};
                --card-accent:{accent};
                --card-bg:{background};
                --card-glow:{glow};">
        <div class="result-label">{escape(label)}</div>
        <div class="result-number">{escape(display_number)}</div>
        <div class="result-description">{escape(description)}</div>
    </div>
    """


# =========================================================
# 12. MAIN LAYOUT
# =========================================================

pyramid_column, results_column = st.columns([1.2, 1], gap="large")

with pyramid_column:
    st.markdown(
        '<div class="panel">'
        '<div class="panel-title">🔺 Number Pyramid</div>'
        '<div class="panel-subtitle">'
        'Built from Possibility 1 (Fixed)'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        make_pyramid(fixed_one),
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="note">ℹ️ The pyramid displays the digits '
        'from Possibility 1. Each digit appears once in its own '
        'separate, colourful box.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

with results_column:
    st.markdown(
        result_card(
            "🔒 POSSIBILITY 1 — FIXED",
            fixed_one,
            "Always the same for the same input.",
            "#119dff",
            "rgba(0, 68, 160, 0.25)",
            "rgba(0, 110, 255, 0.15)",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        result_card(
            "🔒 POSSIBILITY 2 — FIXED",
            fixed_two,
            "Always the same for the same input.",
            "#12dfb4",
            "rgba(0, 130, 100, 0.22)",
            "rgba(0, 255, 190, 0.12)",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        result_card(
            "🔄 POSSIBILITY 3 — ROTATING",
            rotating,
            "Changes when you click Generate.",
            "#e45bff",
            "rgba(95, 22, 160, 0.30)",
            "rgba(206, 50, 255, 0.23)",
        ),
        unsafe_allow_html=True,
    )

    if rotating_count > 0:
        st.caption(
            f"Rotating possibility {state['rotation_index'] + 1} "
            f"of {rotating_count}"
        )

    if st.button("🔄 Generate Next Possibility", use_container_width=True):
        if rotating_count > 0:
            state["rotation_index"] = (
                state["rotation_index"] + 1
            ) % rotating_count

            try:
                save_state(state)
            except OSError:
                st.warning("Could not save rotation state.")

            st.rerun()
        else:
            st.info("There are no additional combinations to rotate through.")


# =========================================================
# 13. FOOTER
# =========================================================

mapping_text = "   ".join(
    f"{digit}→[{choices[0]},{choices[1]}]"
    for digit, choices in MAPPING.items()
)

st.markdown(
    f"""
    <div class="footer-note">
        Input: 3–6 digits &nbsp; | &nbsp;
        Mapping: {escape(mapping_text)}
        <br><br>
        ⭐ Only three possibilities are displayed.
    </div>
    """,
    unsafe_allow_html=True,
)