from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard_data import format_month_label, load_records, select_filters
from team_labels import team_label


st.set_page_config(
    page_title="Environment",
    page_icon=":material/public:",
    layout="wide",
)


df = load_records()
selected_month, filtered, _, _, _ = select_filters(df, key_prefix="env_page")

st.title("Environment Details")
st.caption(f"Period: {format_month_label(selected_month)}")

environment_totals = (
    filtered.groupby("environment_group", as_index=False)["cost_usd"]
    .sum()
    .set_index("environment_group")
    .reindex(["prod", "non-prod"], fill_value=0.0)
    .reset_index()
)

total_spend = float(environment_totals["cost_usd"].sum())
prod_spend = float(
    environment_totals.loc[
        environment_totals["environment_group"] == "prod", "cost_usd"
    ].iloc[0]
)
non_prod_spend = float(
    environment_totals.loc[
        environment_totals["environment_group"] == "non-prod", "cost_usd"
    ].iloc[0]
)

prod_share = prod_spend / total_spend if total_spend > 0 else 0.0
non_prod_share = non_prod_spend / total_spend if total_spend > 0 else 0.0

kpi_1, kpi_2 = st.columns(2)
kpi_1.metric("Prod", f"€{prod_spend:,.0f}", delta=f"{prod_share:.0%} of total")
kpi_2.metric("Non-prod", f"€{non_prod_spend:,.0f}", delta=f"{non_prod_share:.0%} of total")

team_environment = (
    filtered.groupby(["team", "environment_group"], as_index=False)["cost_usd"]
    .sum()
    .sort_values(["team", "environment_group"])
)
team_environment_display = team_environment.copy()
team_environment_display["team"] = team_environment_display["team"].map(team_label)
fig_team_environment = px.bar(
    team_environment_display,
    x="team",
    y="cost_usd",
    color="environment_group",
    barmode="stack",
    title="Cost by team (prod vs non-prod)",
)
fig_team_environment.update_layout(yaxis_title="EUR", xaxis_title="Team")
fig_team_environment.update_traces(hovertemplate="%{x} - %{fullData.name}: €%{y:,.0f}<extra></extra>")
st.plotly_chart(fig_team_environment, use_container_width=True)

provider_environment = (
    filtered.groupby(["provider", "environment_group"], as_index=False)["cost_usd"]
    .sum()
    .sort_values(["provider", "environment_group"])
)
fig_provider_environment = px.bar(
    provider_environment,
    x="provider",
    y="cost_usd",
    color="environment_group",
    barmode="stack",
    title="Cost by provider (prod vs non-prod)",
)
fig_provider_environment.update_layout(yaxis_title="EUR", xaxis_title="Provider")
fig_provider_environment.update_traces(hovertemplate="%{x} - %{fullData.name}: €%{y:,.0f}<extra></extra>")
st.plotly_chart(fig_provider_environment, use_container_width=True)

st.subheader("Environment details")
st.dataframe(
    team_environment_display.sort_values("cost_usd", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "cost_usd": st.column_config.NumberColumn(format="€%.0f"),
    },
)
