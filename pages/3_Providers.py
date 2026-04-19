from __future__ import annotations

import plotly.express as px
import streamlit as st

from brand_colors import PROVIDER_COLORS
from dashboard_data import format_month_label, load_records, select_filters
from team_labels import team_label


st.set_page_config(
    page_title="Providers",
    page_icon=":material/hub:",
    layout="wide",
)


df = load_records()
selected_month, filtered, _, _, _ = select_filters(df, key_prefix="providers_page")

st.title("Provider Details")
st.caption(f"Period: {format_month_label(selected_month)}")

provider_totals = (
    filtered.groupby("provider", as_index=False)["cost_usd"]
    .sum()
    .sort_values("cost_usd", ascending=False)
)
fig_provider_pie = px.pie(
    provider_totals,
    names="provider",
    values="cost_usd",
    hole=0.45,
    title="Cost split by provider",
    color="provider",
    color_discrete_map=PROVIDER_COLORS,
)
fig_provider_pie.update_traces(
    hovertemplate="%{label}: €%{value:,.0f}<br>%{percent}<extra></extra>"
)
st.plotly_chart(fig_provider_pie, use_container_width=True)

provider_team = (
    filtered.groupby(["provider", "team"], as_index=False)["cost_usd"]
    .sum()
    .sort_values(["provider", "cost_usd"], ascending=[True, False])
)
provider_team_display = provider_team.copy()
provider_team_display["team"] = provider_team_display["team"].map(team_label)
fig_provider_team = px.bar(
    provider_team_display,
    x="provider",
    y="cost_usd",
    color="team",
    barmode="stack",
    title="Provider x team breakdown",
)
fig_provider_team.update_layout(yaxis_title="EUR", xaxis_title="Provider")
fig_provider_team.update_traces(hovertemplate="%{x} - %{fullData.name}: €%{y:,.0f}<extra></extra>")
st.plotly_chart(fig_provider_team, use_container_width=True)

st.subheader("Provider x team table")
pivot = provider_team.pivot_table(
    index="provider",
    columns="team",
    values="cost_usd",
    aggfunc="sum",
    fill_value=0,
)
pivot = pivot.rename(columns=team_label)
pivot["Total"] = pivot.sum(axis=1)
pivot = pivot.sort_values("Total", ascending=False)

st.dataframe(
    pivot,
    use_container_width=True,
    column_config={
        column: st.column_config.NumberColumn(format="€%.0f")
        for column in pivot.columns
    },
)
