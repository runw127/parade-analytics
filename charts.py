import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from data import COLUMN_ORDER, LABELS

pio.templates.default = "none"

COLORS = px.colors.qualitative.Safe
DAY_COLORS = {day: COLORS[i % len(COLORS)] for i, day in enumerate(COLUMN_ORDER["day"])}
INK, MUTED, GRID, BACKGROUND = "#1f1f1f", "#6f6e69", "#e6e5df", "#ffffff"
LOCATION_COLORS = dict(zip(COLUMN_ORDER["location"], ["#6250d6", "#eda100"], strict=True))


def _style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", size=13, color=INK),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        bargap=0.25,
        plot_bgcolor=BACKGROUND,
        paper_bgcolor=BACKGROUND,
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(gridcolor=GRID, tickfont_color=MUTED, title_font_color=MUTED)
    fig.update_yaxes(gridcolor=GRID, tickfont_color=MUTED, title_font_color=MUTED)
    return fig


def empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(color=MUTED, size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _style(fig)


def _bars(fig: go.Figure) -> go.Figure:
    return fig.update_traces(marker_cornerradius=4, marker_line_width=0, selector=dict(type="bar"))


def compact(value: float) -> str:
    return f"{value / 1000:,.0f}k" if value >= 1000 else f"{value:,.0f}"


def day_location_chart(df: pd.DataFrame, y_max: float) -> go.Figure:
    locations = [loc for loc in COLUMN_ORDER["location"] if loc in set(df["location"].astype(str))]
    days = [d for d in COLUMN_ORDER["day"] if d in set(df["day"].astype(str))]
    fig = go.Figure()
    for location in locations:
        side = df[df["location"] == location].set_index("day").reindex(days)
        values = side["visitors"].fillna(0)
        fig.add_trace(
            go.Bar(
                x=days,
                y=values,
                name=location,
                marker_color=LOCATION_COLORS[location],
                text=[compact(v) for v in values],
                textposition="outside",
                textfont_color=MUTED,
                cliponaxis=False,
                hovertemplate=f"{location}<br>%{{x}}<br>%{{y:,.0f}} visitors<extra></extra>",
            )
        )

    fig = _bars(_style(fig, height=340))
    fig.update_yaxes(range=[0, y_max * 1.15], visible=False)
    fig.update_xaxes(tickvals=days, showgrid=False)
    fig.update_layout(barmode="group", bargroupgap=0.08, showlegend=len(locations) > 1)
    if len(locations) == 1:
        fig.add_annotation(
            text=locations[0],
            x=0,
            xref="paper",
            y=1,
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            showarrow=False,
            font=dict(size=13, color=INK),
        )
    return fig.update_layout(margin=dict(t=36))


def dwell_lines_chart(df: pd.DataFrame) -> go.Figure:
    days = [d for d in COLUMN_ORDER["day"] if d in set(df["day"].astype(str))]
    fig = px.line(
        df,
        x="dwell_time",
        y="share",
        color="day",
        markers=True,
        category_orders={"dwell_time": COLUMN_ORDER["dwell_time"], "day": days},
        color_discrete_map=DAY_COLORS,
        labels={**LABELS, "share": "Share of the day's visitors (%)"},
        custom_data=["visitors"],
    )
    fig.update_traces(
        line_width=2,
        marker=dict(size=8, line=dict(width=2, color=BACKGROUND)),
        hovertemplate="%{y:.1f}% %{fullData.name}<br>%{customdata[0]:,.0f} people<extra></extra>",
    )
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(ticksuffix="%", rangemode="tozero")
    return _style(fig, height=360)


SEQUENTIAL = ["#eef4fc", "#b7d3f6", "#6da7ec", "#2a78d6", "#1c5cab", "#0d366b"]


def dwell_share_heatmap(df: pd.DataFrame, by: str, rows: list[str], row_labels: list[str]) -> go.Figure:
    bands = [b for b in COLUMN_ORDER["dwell_time"] if b in set(df["dwell_time"].astype(str))]
    table = df.assign(**{by: df[by].astype(str), "dwell_time": df["dwell_time"].astype(str)})
    share = table.pivot(index=by, columns="dwell_time", values="share").reindex(index=rows, columns=bands)
    visitors = table.pivot(index=by, columns="dwell_time", values="visitors").reindex(index=rows, columns=bands)
    group = LABELS[by].lower()
    fig = go.Figure(
        go.Heatmap(
            z=share.fillna(0).values,
            x=bands,
            y=rows,
            customdata=visitors.fillna(0).values,
            colorscale=[[i / (len(SEQUENTIAL) - 1), c] for i, c in enumerate(SEQUENTIAL)],
            zmin=0,
            showscale=False,
            xgap=2,
            ygap=2,
            texttemplate="%{z:.0f}%",
            hovertemplate=(
                f"%{{y}}, stayed %{{x}}<br>%{{z:.1f}}% of this {group}<br>%{{customdata:,.0f}} visitors<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(title_text=LABELS["dwell_time"], showgrid=False)
    fig.update_yaxes(
        title_text=LABELS[by],
        showgrid=False,
        tickvals=rows,
        ticktext=row_labels,
        autorange="reversed",
    )
    return _style(fig, height=max(300, 40 * len(rows) + 100))


LINE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]


def share_lines_chart(df: pd.DataFrame, by: str, rows: list[str], row_labels: list[str]) -> go.Figure:
    bands = [b for b in COLUMN_ORDER["dwell_time"] if b in set(df["dwell_time"].astype(str))]
    table = df.assign(**{by: df[by].astype(str), "dwell_time": df["dwell_time"].astype(str)})
    fig = go.Figure()
    for row, label, color in zip(rows, row_labels, LINE_COLORS, strict=False):
        line = table[table[by] == row].set_index("dwell_time").reindex(bands)
        fig.add_trace(
            go.Scatter(
                x=bands,
                y=line["share"].fillna(0),
                name=label,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=8, color=color, line=dict(width=2, color=BACKGROUND)),
                customdata=line["visitors"].fillna(0),
                hovertemplate=f"{row}: %{{y:.1f}}%<br>%{{customdata:,.0f}} visitors<extra></extra>",
            )
        )
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text=LABELS["dwell_time"], showgrid=False)
    fig.update_yaxes(
        title_text=f"Share of each {LABELS[by].lower()}'s visitors (%)", ticksuffix="%", rangemode="tozero"
    )
    return _style(fig, height=380)
