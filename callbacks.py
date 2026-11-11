from dash import Dash, Input, Output

import charts
import data

NO_DATA = "No visitors match these filters"


def update_comparison(location, visitor_type):
    df = data.scope(data.load_data(), location, visitor_type)
    if df.empty:
        return charts.empty_figure(NO_DATA)
    y_max = data.breakdown(data.load_data(), "location", "day")["visitors"].max()
    return charts.day_location_chart(data.breakdown(df, "location", "day"), y_max)


def update_dwell(location, visitor_type, compare):
    days = data.COMPARISON_DAYS[compare]
    df = data.scope(data.load_data(), location, visitor_type)
    df = df[df["day"].isin(days) & (df["dwell_time"] != "Unknown")]
    if df.empty:
        return charts.empty_figure(NO_DATA)
    return charts.dwell_lines_chart(data.breakdown(df, "dwell_time", "day"))


def update_countries(location, day):
    df = data.scope(data.load_data(), location, "International")
    df = df[(df["day"] == day) & (df["dwell_time"] != "Unknown")]
    if df.empty:
        return charts.empty_figure(NO_DATA)
    totals = df.groupby("country_of_origin", observed=True)["visitors"].sum().nlargest(5)
    top = df[df["country_of_origin"].isin(totals.index)]
    countries = [str(c) for c in totals.index]
    labels = [f"{c} · {charts.compact(v)}" for c, v in zip(countries, totals, strict=True)]
    breakdown = data.breakdown(top, "dwell_time", "country_of_origin")
    return charts.dwell_share_heatmap(breakdown, "country_of_origin", countries, labels)


def update_age_dwell(location, visitor_type, day):
    df = data.scope(data.load_data(), location, visitor_type)
    df = df[
        (df["day"] == day)
        & (df["visitor_type"] != "International")
        & (df["age_band"] != "Not stated")
        & (df["dwell_time"] != "Unknown")
    ]
    if df.empty:
        return charts.empty_figure("Age is not recorded for international visitors")
    ages = [a for a in data.COLUMN_ORDER["age_band"] if a in set(df["age_band"].astype(str))]
    return charts.share_lines_chart(data.breakdown(df, "dwell_time", "age_band"), "age_band", ages, ages)


def register_callbacks(app: Dash) -> None:
    scope = [Input("a-location", "value"), Input("a-visitor-type", "value")]
    app.callback(Output("a-day-location", "figure"), *scope)(update_comparison)
    app.callback(Output("a-dwell", "figure"), *scope, Input("a-compare", "value"))(update_dwell)

    safety_scope = [Input("s-location", "value"), Input("s-visitor-type", "value")]
    app.callback(Output("s-day-location", "figure"), *safety_scope)(update_comparison)
    app.callback(Output("s-countries", "figure"), Input("s-location", "value"), Input("s-who-day", "value"))(
        update_countries
    )
    app.callback(Output("s-age-dwell", "figure"), *safety_scope, Input("s-age-dwell-day", "value"))(update_age_dwell)
