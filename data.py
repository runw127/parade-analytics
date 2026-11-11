from datetime import datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent / "data" / "Tourism Sample Data 2026.csv"


def day_labels(dates: pd.Series) -> dict[str, str]:
    parsed = {value: datetime.strptime(value, "%d/%m/%Y") for value in dates.unique()}
    ordered = sorted(parsed, key=lambda value: (parsed[value].month == 3 and parsed[value].day == 17, parsed[value]))
    return {
        value: f"Parade {parsed[value].year}"
        if parsed[value].month == 3 and parsed[value].day == 17
        else f"Normal day {parsed[value].day} {parsed[value]:%b %Y}"
        for value in ordered
    }


DATE_TO_DAY = day_labels(pd.read_csv(DATA_PATH, usecols=["event_date"], keep_default_na=False)["event_date"])
DAYS = list(DATE_TO_DAY.values())
DEFAULT_DAY = DATE_TO_DAY[max(DATE_TO_DAY, key=lambda value: datetime.strptime(value, "%d/%m/%Y"))]
LOCATIONS = ["College Green", "O'Connell Bridge"]

COLUMN_ORDER = {
    "day": DAYS,
    "location": LOCATIONS,
    "visitor_type": ["Local", "Domestic", "International"],
    "age_band": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+", "Not stated"],
    "dwell_time": [
        "0-10 min",
        "10-30 min",
        "30-60 min",
        "60-120 min",
        "120-240 min",
        "240-480 min",
        "480-600 min",
        "> 600 min",
        "Unknown",
    ],
    "gender": ["Female", "Male", "Not stated"],
}

LABELS = {
    "day": "Day",
    "age_band": "Age band",
    "dwell_time": "Time spent",
    "country_of_origin": "Country",
    "visitors": "Visitors",
    "share": "Share (%)",
}

TOP_COUNTRIES = 15


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    date_to_day = day_labels(df["event_date"])
    df["day"] = df["event_date"].map(date_to_day)
    df["location"] = df["location"].replace({"O'Connel Bridge": "O'Connell Bridge"})
    df["gender"] = df["gender"].replace({"F": "Female", "M": "Male", "N": "Not stated"})
    df["age_band"] = df["age_band"].replace({"N/A": "Not stated", "": "Not stated"})
    df["dwell_time"] = df["dwell_time"].replace({"null": "Unknown", "": "Unknown"})

    for column, order in {**COLUMN_ORDER, "day": list(date_to_day.values())}.items():
        unexpected = set(df[column].unique()) - set(order)
        if unexpected:
            raise ValueError(f"Unexpected {column} values: {sorted(unexpected)}")
        df[column] = pd.Categorical(df[column], categories=order, ordered=True)
    df["country_of_origin"] = df["country_of_origin"].astype("category")
    return df.drop(columns="event_date")


@lru_cache(maxsize=1)
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    raw = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    return clean(raw)


def breakdown(df: pd.DataFrame, by: str, split: str | None = None) -> pd.DataFrame:
    if split == by:
        split = None
    if by == "country_of_origin":
        top = df.groupby(by, observed=True)["visitors"].sum().nlargest(TOP_COUNTRIES).index
        df = df[df[by].isin(top)]

    columns = [by] if split is None else [split, by]
    out = df.groupby(columns, observed=True)["visitors"].sum().reset_index()
    if split is None:
        out["share"] = 100 * out["visitors"] / out["visitors"].sum()
    else:
        out["share"] = 100 * out["visitors"] / out.groupby(split, observed=True)["visitors"].transform("sum")

    if by == "country_of_origin":
        totals = out.groupby(by, observed=True)["visitors"].transform("sum")
        out = out.assign(_total=totals).sort_values("_total", ascending=False).drop(columns="_total")
    return out.reset_index(drop=True)


ALL = "all"


def comparison_days(days: list[str]) -> dict[str, list[str]]:
    choices = {"all": days, "parades": [day for day in days if day.startswith("Parade ")]}
    for year in sorted({int(day[-4:]) for day in days}):
        year_days = [day for day in days if day.endswith(str(year))]
        has_parade = any(day.startswith("Parade ") for day in year_days)
        has_normal = any(day.startswith("Normal day ") for day in year_days)
        if has_parade and has_normal:
            choices[str(year)] = year_days
    return choices


COMPARISON_DAYS = comparison_days(DAYS)


def scope(df: pd.DataFrame, location: str = ALL, visitor_type: str = ALL) -> pd.DataFrame:
    if location != ALL:
        df = df[df["location"] == location]
    if visitor_type != ALL:
        df = df[df["visitor_type"] == visitor_type]
    return df
