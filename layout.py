from dash import dcc, html

from data import ALL, COLUMN_ORDER, COMPARISON_DAYS, DAYS, DEFAULT_DAY, LOCATIONS

COMPARE_OPTIONS = [
    {"label": "All days", "value": "all"},
    {"label": "Parade days only", "value": "parades"},
    *[
        {"label": f"{year} parade vs normal days", "value": year}
        for year in COMPARISON_DAYS
        if year not in {"all", "parades"}
    ],
]

TAB_CLASSES = {"className": "tab", "selected_className": "tab--selected"}


def control(label: str, component, control_id: str) -> html.Div:
    return html.Div([html.Label(label, htmlFor=control_id, className="control-label"), component], className="control")


def card(title, *children) -> html.Div:
    return html.Div([html.H2(title), *children], className="card")


def graph(graph_id: str) -> dcc.Graph:
    return dcc.Graph(id=graph_id, config={"displaylogo": False})


def dropdown(dropdown_id: str, options, value) -> dcc.Dropdown:
    return dcc.Dropdown(id=dropdown_id, options=options, value=value, clearable=False)


def section(*children) -> html.Section:
    return html.Section(list(children), className="section")


def scope_filters(prefix: str) -> html.Div:
    location, visitor_type = f"{prefix}-location", f"{prefix}-visitor-type"
    filters = html.Div(
        [
            html.Div(
                [
                    control(
                        "Location",
                        dropdown(location, [{"label": "All locations", "value": ALL}] + LOCATIONS, ALL),
                        location,
                    ),
                    control(
                        "Visitor type",
                        dropdown(
                            visitor_type,
                            [{"label": "All visitor types", "value": ALL}] + COLUMN_ORDER["visitor_type"],
                            ALL,
                        ),
                        visitor_type,
                    ),
                ],
                className="controls",
            ),
        ],
        className="card",
    )
    coverage = html.Div(
        [
            html.Strong("About this data", className="note-title"),
            html.P(
                "Visitor estimates for College Green and O'Connell Bridge on the dates in the CSV.",
                className="note-text",
            ),
        ],
        className="card note",
        role="note",
    )
    return html.Div([filters, coverage], className="filters-column")


def time_spent_section(prefix: str) -> html.Section:
    compare = f"{prefix}-compare"
    return section(
        html.Div(
            control("Traffic Distribution", dropdown(compare, COMPARE_OPTIONS, "all"), compare),
            className="controls section-controls",
        ),
        card("Share of each day's visitors by time spent", graph(f"{prefix}-dwell")),
    )


def traffic_management_tab() -> list:
    return [
        html.Div(
            [scope_filters("a"), card("Visitors Overview", graph("a-day-location"))],
            className="row-third-two-thirds",
        ),
        time_spent_section("a"),
    ]


def safety_tab() -> list:
    return [
        html.Div(
            [scope_filters("s"), card("Visitors Overview", graph("s-day-location"))],
            className="row-third-two-thirds",
        ),
        section(
            html.Div(
                control("Day", dropdown("s-age-dwell-day", DAYS, DEFAULT_DAY), "s-age-dwell-day"),
                className="controls section-controls",
            ),
            card(
                "Time spent by age band: % of each age group (Local and Domestic, age stated)",
                graph("s-age-dwell"),
            ),
        ),
        section(
            html.Div(
                control("Day", dropdown("s-who-day", DAYS, DEFAULT_DAY), "s-who-day"),
                className="controls section-controls",
            ),
            card(
                "Time spent by country: % of each country's visitors (International, top 5 countries)",
                graph("s-countries"),
            ),
        ),
    ]


def build_layout() -> html.Div:
    return html.Div(
        [
            html.Header(html.H1("St Patrick's Day Parade: Visitor Analysis")),
            dcc.Tabs(
                [
                    dcc.Tab(traffic_management_tab(), label="Traffic Management", value="operations", **TAB_CLASSES),
                    dcc.Tab(safety_tab(), label="Event Safety Lead", value="safety", **TAB_CLASSES),
                ],
                value="operations",
                className="tabs",
            ),
        ],
        className="page",
    )
