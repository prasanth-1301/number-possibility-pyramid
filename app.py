
import itertools
import json
import random
import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from io import StringIO

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Number Possibility Pyramid",
    page_icon="🔢",
    layout="centered",
)


# =========================================================
# NUMBER MAPPING
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

HISTORY_FILE = Path("historical_results.json")
ROTATION_FILE = Path("rotation_state.json")

CHART_URL = (
    "https://a1sattaking.com/"
    "satta-king-yearly-chart/tamil-nadu/{}"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


# =========================================================
# DESIGN
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #101426, #17233b);
    }

    h1, h2, h3, p, label {
        color: white !important;
    }

    .result-card {
        background: #202b46;
        border: 1px solid #435477;
        border-radius: 14px;
        padding: 16px;
        margin: 10px 0;
        text-align: center;
    }

    .result-label {
        color: #d8e4ff;
        font-size: 15px;
        margin-bottom: 8px;
    }

    .result-number {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: 4px;
        color: #74f7d4;
        overflow-wrap: anywhere;
    }

    .pyramid {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        margin: 18px 0 24px;
    }

    .pyramid-row {
        display: flex;
        justify-content: center;
        gap: 7px;
    }

    .digit-box {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 9px;
        background: linear-gradient(135deg, #284f91, #543f94);
        border: 1px solid #82b6ff;
        color: white;
        font-size: 21px;
        font-weight: bold;
    }

    .small-note {
        color: #b7c7e8;
        text-align: center;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HISTORICAL DATA PARSER
# =========================================================

def parse_calendar(rows, year):
    """Parse the source layout: year, month headings, then day rows."""

    if not rows:
        return []

    header = [
        str(value).strip().lower()
        for value in rows[0]
    ]

    month_columns = {}

    for column_index, value in enumerate(header):
        month = value[:3]

        if month in MONTHS:
            month_columns[column_index] = MONTHS[month]

    if len(month_columns) != 12:
        return []

    records = []

    for row in rows[1:]:
        if not row:
            continue

        day_text = str(row[0]).strip()

        if not re.fullmatch(r"\d{1,2}", day_text):
            continue

        day = int(day_text)

        for column_index, month in month_columns.items():
            if column_index >= len(row):
                continue

            result = str(row[column_index]).strip()

            # Accept only actual two-digit results.
            if not re.fullmatch(r"\d{2}", result):
                continue

            try:
                result_date = date(year, month, day)
            except ValueError:
                continue

            records.append({
                "date": result_date.isoformat(),
                "winning_number": result,
            })

    return records


def parse_html(html, year):
    soup = BeautifulSoup(html, "html.parser")

    for table in soup.find_all("table"):
        rows = []

        for tr in table.find_all("tr"):
            cells = [
                cell.get_text(" ", strip=True)
                for cell in tr.find_all(["th", "td"])
            ]

            if cells:
                rows.append(cells)

        records = parse_calendar(rows, year)

        if records:
            return records

    # Fallback table parser.
    try:
        tables = pd.read_html(StringIO(html))

        for table in tables:
            table = table.fillna("")

            rows = [
                [str(value).strip() for value in row]
                for row in table.values.tolist()
            ]

            records = parse_calendar(rows, year)

            if records:
                return records

            headers = [
                str(column).strip()
                for column in table.columns
            ]

            records = parse_calendar([headers] + rows, year)

            if records:
                return records

    except (ValueError, ImportError):
        pass

    return []


def fetch_year(year):
    url = CHART_URL.format(year)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    records = parse_html(response.text, year)

    if not records:
        raise RuntimeError(
            f"No published two-digit results could be read for {year}. "
            "The chart may contain only unavailable entries."
        )

    return records


# =========================================================
# SAVE AND LOAD HISTORY
# =========================================================

def load_saved_history():
    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(
            HISTORY_FILE.read_text(encoding="utf-8")
        )

        if not isinstance(data, list):
            return []

        valid = []

        for item in data:
            if not isinstance(item, dict):
                continue

            result = str(item.get("winning_number", ""))
            date_text = item.get("date", "")

            if not re.fullmatch(r"\d{2}", result):
                continue

            try:
                date.fromisoformat(date_text)
            except (ValueError, TypeError):
                continue

            valid.append({
                "date": date_text,
                "winning_number": result,
            })

        return valid

    except (OSError, ValueError):
        return []


def save_history(records):
    try:
        HISTORY_FILE.write_text(
            json.dumps(records, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_history():
    """
    Try each year in the previous three-year window.
    Merge downloaded records with saved records.
    """

    today = date.today()
    cutoff = today - timedelta(days=365 * 3)

    by_date = {}
    errors = []

    # Keep existing valid records inside the date window.
    for item in load_saved_history():
        try:
            result_date = date.fromisoformat(item["date"])

            if cutoff <= result_date <= today:
                by_date[item["date"]] = item

        except (ValueError, KeyError):
            continue

    downloaded_count = 0

    for year in range(cutoff.year, today.year + 1):
        try:
            for item in fetch_year(year):
                result_date = date.fromisoformat(item["date"])

                if cutoff <= result_date <= today:
                    by_date[item["date"]] = item
                    downloaded_count += 1

        except Exception as error:
            errors.append(f"{year}: {error}")

    records = [
        by_date[key]
        for key in sorted(by_date)
    ]

    if records:
        saved = save_history(records)

        if downloaded_count:
            source = "Downloaded and merged with saved history"
        else:
            source = "Saved history"

        if not saved:
            errors.append(
                "Could not save historical_results.json."
            )

        return records, errors, source

    return [], errors, "Unavailable"


# =========================================================
# POSSIBILITIES
# =========================================================

def fixed_results(number):
    first = "".join(MAPPING[d][0] for d in number)
    second = "".join(MAPPING[d][1] for d in number)

    return first, second


def rank_candidates(number, history):
    combinations = {
        "".join(values)
        for values in itertools.product(
            *(MAPPING[digit] for digit in number)
        )
    }

    first, second = fixed_results(number)

    combinations.discard(number)
    combinations.discard(first)
    combinations.discard(second)

    first_counts = Counter()
    second_counts = Counter()

    for record in history:
        result = str(record.get("winning_number", ""))

        if re.fullmatch(r"\d{2}", result):
            first_counts[result[0]] += 1
            second_counts[result[1]] += 1

    def score(candidate):
        total = 0

        for index, digit in enumerate(candidate):
            if index % 2 == 0:
                total += first_counts[digit]
            else:
                total += second_counts[digit]

        return total

    return sorted(
        combinations,
        key=lambda item: (-score(item), item),
    )


# =========================================================
# MIXED-DIGIT PYRAMID
# =========================================================

def make_mixed_pyramid_number(length=None):
    """
    Generate 10 random digits from 1 to 9.
    The generated pyramid is saved per input number.
    """
    return "".join(
        random.choice("123456789")
        for _ in range(10)
    )


def show_pyramid(number):
    """Display exactly four rows containing 1, 2, 3, and 4 boxes."""

    st.markdown("### 🔺 Number Pyramid")

    st.markdown(
        '<div class="small-note">'
        'Every box contains a randomly mixed digit from 1 to 9'
        '</div>',
        unsafe_allow_html=True,
    )

    digits = list(str(number))[:10]

    while len(digits) < 10:
        digits.append(random.choice("123456789"))

    html = '<div class="pyramid">'
    position = 0

    for row_length in range(1, 5):
        html += '<div class="pyramid-row">'

        for digit in digits[position:position + row_length]:
            html += f'<span class="digit-box">{digit}</span>'

        html += '</div>'
        position += row_length

    html += '</div>'

    st.markdown(html, unsafe_allow_html=True)


def show_result(label, number):
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">{label}</div>
            <div class="result-number">{number}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# ROTATION STATE
# =========================================================

def load_rotation_state():
    try:
        if ROTATION_FILE.exists():
            data = json.loads(
                ROTATION_FILE.read_text(encoding="utf-8")
            )

            if isinstance(data, dict):
                return data

    except (OSError, ValueError):
        pass

    return {}


def save_rotation_state(state):
    try:
        ROTATION_FILE.write_text(
            json.dumps(state, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


# =========================================================
# MAIN PAGE
# =========================================================

st.title("🔢 Number Possibility Pyramid")
st.caption("Enter a number to generate three possibilities")


# ---------------------------------------------------------
# LOAD HISTORICAL RESULTS QUIETLY
# ---------------------------------------------------------

history, history_errors, history_source = fetch_history()


# ---------------------------------------------------------
# INPUT
# ---------------------------------------------------------

st.markdown("---")
st.subheader("Enter your number")

original = st.text_input(
    "Number (3, 4, 5, or 6 digits)",
    max_chars=6,
    placeholder="Example: 1563",
).strip()

valid_number = (
    original.isascii()
    and original.isdigit()
    and len(original) in (3, 4, 5, 6)
)

st.caption(
    "Enter 3, 4, 5, or 6 digits. Leading zeros are preserved."
)


# ---------------------------------------------------------
# GENERATE
# ---------------------------------------------------------

if st.button(
    "✨ Generate Possibilities",
    type="primary",
    use_container_width=True,
):
    if not valid_number:
        st.error("Enter exactly 3, 4, 5, or 6 digits.")

        st.session_state.pop("last_input", None)
        st.session_state.pop("last_results", None)
        st.session_state.pop("last_pyramid", None)

    else:
        first, second = fixed_results(original)
        candidates = rank_candidates(original, history)

        if first == second:
            st.error(
                "The two fixed possibilities are identical."
            )

        elif not candidates:
            st.error(
                "No distinct third possibility is available "
                "for this input."
            )

        else:
            state = load_rotation_state()

            # Rotate Possibility 3 for this input.
            try:
                index = int(state.get(original, 0))
            except (TypeError, ValueError):
                index = 0

            third = candidates[index % len(candidates)]

            state[original] = index + 1

            # FIX: Keep a separate, permanent pyramid for each input.
            pyramid_key = f"pyramid_{original}"

            if pyramid_key not in state:
                state[pyramid_key] = make_mixed_pyramid_number()

            # Save both rotation and pyramid state.
            save_rotation_state(state)

            pyramid_number = state[pyramid_key]

            st.session_state["last_input"] = original
            st.session_state["last_results"] = [
                first,
                second,
                third,
            ]
            st.session_state["last_pyramid"] = pyramid_number
            st.session_state["last_used_history"] = bool(history)


# ---------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------

if (
    st.session_state.get("last_input") == original
    and st.session_state.get("last_results")
):
    first, second, third = st.session_state["last_results"]
    pyramid_number = st.session_state["last_pyramid"]

    st.markdown("---")

    # The pyramid stays the same for the same input.
    show_pyramid(pyramid_number)

    st.markdown("## Your Three Possibilities")

    show_result("Possibility 1 — Fixed", first)
    show_result("Possibility 2 — Fixed", second)
    show_result("Possibility 3 — Rotating", third)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Only published historical results are included. "
    "Missing chart entries are not invented, and past results "
    "do not guarantee future outcomes."
)
