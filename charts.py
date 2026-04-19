from __future__ import annotations

import json
import uuid

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from brand_colors import PROVIDER_COLORS, provider_color_sequence


def _stacked_pivot(
    frame: pd.DataFrame,
    category_col: str,
    series_col: str,
    value_col: str,
) -> pd.DataFrame:
    pivot = frame.pivot_table(
        index=category_col,
        columns=series_col,
        values=value_col,
        aggfunc="sum",
        fill_value=0.0,
    )

    if pivot.empty:
        return pivot

    category_order = pivot.sum(axis=1).sort_values(ascending=False).index
    series_order = pivot.sum(axis=0).sort_values(ascending=False).index
    return pivot.loc[category_order, series_order]


def build_vertical_stacked_options(
    frame: pd.DataFrame,
    category_col: str,
    series_col: str,
    value_col: str,
    title: str,
) -> dict:
    pivot = _stacked_pivot(frame, category_col, series_col, value_col)

    categories = pivot.index.tolist()
    series_names = pivot.columns.tolist()

    series = []
    for name in series_names:
        series.append(
            {
                "name": str(name),
                "type": "bar",
                "stack": "total",
                "label": {"show": False},
                "emphasis": {"focus": "series"},
                "barMaxWidth": 52,
                "data": [int(round(float(value))) for value in pivot[name].tolist()],
            }
        )

    options = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
        },
        "legend": {
            "data": series_names,
            "left": "center",
            "bottom": 4,
            "orient": "horizontal",
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "top": 64,
            "bottom": 72,
            "containLabel": True,
        },
        "xAxis": {"type": "category", "data": categories},
        "yAxis": {
            "type": "value",
            "axisLabel": {"formatter": "€{value}"},
        },
        "series": series,
        "title": {"text": title, "left": "center", "top": 0},
    }

    if series_col == "provider":
        options["color"] = provider_color_sequence([str(name) for name in series_names])

    return options


def _render_echarts(options: dict, height: int) -> None:
    chart_id = f"echarts_{uuid.uuid4().hex}"
    options_json = json.dumps(options)

    html = f"""
    <div id=\"{chart_id}\" style=\"width:100%;height:{height}px;\"></div>
    <script>
    (function() {{
        const container = document.getElementById("{chart_id}");
        const options = {options_json};
        options.tooltip.formatter = function(params) {{
            if (!params || params.length === 0) {{
                return '';
            }}
            let total = 0;
            const lines = [params[0].axisValue];
            params.forEach(function(item) {{
                const value = Number(item.value || 0);
                total += value;
                lines.push(
                    item.marker + ' ' + item.seriesName + ': €' +
                    value.toLocaleString(undefined, {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }})
                );
            }});
            lines.push(
                '<b>Total: €' +
                total.toLocaleString(undefined, {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }}) +
                '</b>'
            );
            return lines.join('<br/>');
        }};

        const renderChart = () => {{
            const chart = window.echarts.getInstanceByDom(container) || window.echarts.init(container);
            chart.setOption(options);
            window.addEventListener("resize", () => chart.resize());
        }};

        if (window.echarts) {{
            renderChart();
            return;
        }}

        const existingScript = document.querySelector("script[data-echarts-cdn='true']");
        if (existingScript) {{
            if (window.echarts) {{
                renderChart();
            }} else {{
                existingScript.addEventListener("load", renderChart, {{ once: true }});
            }}
            return;
        }}

        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js";
        script.async = true;
        script.dataset.echartsCdn = "true";
        script.onload = renderChart;
        document.head.appendChild(script);
    }})();
    </script>
    """

    components.html(html, height=height + 16)


def render_vertical_stacked_bar(
    frame: pd.DataFrame,
    category_col: str,
    series_col: str,
    value_col: str,
    title: str,
    height: int = 460,
) -> None:
    if frame.empty:
        st.info("No data to display.")
        return

    options = build_vertical_stacked_options(
        frame=frame,
        category_col=category_col,
        series_col=series_col,
        value_col=value_col,
        title=title,
    )

    try:
        _render_echarts(options, height=height)
    except Exception:
        color_map = PROVIDER_COLORS if series_col == "provider" else None
        fig = px.bar(
            frame,
            x=category_col,
            y=value_col,
            color=series_col,
            barmode="stack",
            title=title,
            color_discrete_map=color_map,
        )
        fig.update_layout(
            yaxis_title="EUR",
            legend={
                "orientation": "h",
                "x": 0.5,
                "xanchor": "center",
                "y": -0.2,
                "yanchor": "top",
            },
            margin={"b": 110},
        )
        fig.update_traces(hovertemplate="%{fullData.name}<br>%{x}: €%{y:,.0f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)
