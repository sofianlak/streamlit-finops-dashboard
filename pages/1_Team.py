from __future__ import annotations

import plotly.express as px
import streamlit as st

from charts import render_vertical_stacked_bar
from dashboard_data import format_month_label, load_records, select_filters
from team_labels import team_label


st.set_page_config(
    page_title="Team",
    page_icon=":material/groups:",
    layout="wide",
)


df = load_records()
selected_month, filtered, _, _, _ = select_filters(df, key_prefix="team_page")

st.title("Team Details")
st.caption(f"Period: {format_month_label(selected_month)}")

team_totals = (
    filtered.groupby("team", as_index=False)["cost_usd"]
    .sum()
    .sort_values("cost_usd", ascending=False)
)
team_totals_display = team_totals.copy()
team_totals_display["team"] = team_totals_display["team"].map(team_label)
fig_team_totals = px.bar(
    team_totals_display,
    x="team",
    y="cost_usd",
    title="Total cost by team",
    text_auto=".0f",
)
fig_team_totals.update_layout(yaxis_title="EUR", xaxis_title="Team")
fig_team_totals.update_traces(hovertemplate="%{x}: €%{y:,.0f}<extra></extra>")
st.plotly_chart(fig_team_totals, use_container_width=True)

team_provider = (
    filtered.groupby(["team", "provider"], as_index=False)["cost_usd"]
    .sum()
    .sort_values(["team", "cost_usd"], ascending=[True, False])
)
team_provider_display = team_provider.copy()
team_provider_display["team"] = team_provider_display["team"].map(team_label)
render_vertical_stacked_bar(
    frame=team_provider_display,
    category_col="team",
    series_col="provider",
    value_col="cost_usd",
    title="Team x provider breakdown",
    height=500,
)

st.subheader("Team / provider / service details")
service_detail = (
    filtered.groupby(["team", "provider", "service"], as_index=False)["cost_usd"]
    .sum()
    .sort_values("cost_usd", ascending=False)
)
service_detail_display = service_detail.copy()
service_detail_display["team"] = service_detail_display["team"].map(team_label)
st.dataframe(
    service_detail_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "cost_usd": st.column_config.NumberColumn(format="€%.0f"),
    },
)
