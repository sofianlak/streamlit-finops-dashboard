from __future__ import annotations

import streamlit as st

from charts import render_vertical_stacked_bar
from dashboard_data import format_month_label, load_records, select_filters
from dashboard_utils import filter_month, month_total_cost, previous_month_label, with_environment_group
from kpi_cards import render_team_kpi_cards
from team_labels import team_label


st.set_page_config(
    page_title="FinOps Dashboard",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
)


df = load_records()
(
    selected_month,
    filtered,
    selected_teams,
    selected_providers,
    selected_environment_groups,
) = select_filters(df, key_prefix="home")

st.title("FinOps Dashboard")
st.caption("Monthly cloud spend overview")

st.subheader(f"Period: {format_month_label(selected_month)}")

total_spend = float(filtered["cost_usd"].sum())
prev_month = previous_month_label(selected_month)
prev_month_display = format_month_label(prev_month)
prev_total_spend = month_total_cost(
    df,
    prev_month,
    teams=selected_teams,
    providers=selected_providers,
    environment_groups=selected_environment_groups,
)
delta_abs = total_spend - prev_total_spend
delta_pct = (delta_abs / prev_total_spend * 100) if prev_total_spend > 0 else None

selected_year = int(selected_month[:4])
selected_month_number = int(selected_month[5:7])
previous_year = selected_year - 1

filtered_all = with_environment_group(df)
filtered_all = filtered_all[
    filtered_all["team"].isin(selected_teams)
    & filtered_all["provider"].isin(selected_providers)
    & filtered_all["environment_group"].isin(selected_environment_groups)
].copy()
filtered_all["year"] = filtered_all["date"].dt.year
filtered_all["month_number"] = filtered_all["date"].dt.month

current_ytd_spend = float(
    filtered_all.loc[
        (filtered_all["year"] == selected_year)
        & (filtered_all["month_number"] <= selected_month_number),
        "cost_usd",
    ].sum()
)
previous_ytd_spend = float(
    filtered_all.loc[
        (filtered_all["year"] == previous_year)
        & (filtered_all["month_number"] <= selected_month_number),
        "cost_usd",
    ].sum()
)
ytd_delta_abs = current_ytd_spend - previous_ytd_spend
ytd_delta_pct = (
    (ytd_delta_abs / previous_ytd_spend) * 100 if previous_ytd_spend > 0 else None
)

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
kpi_1.metric(
    "Monthly spend",
    f"€{total_spend:,.0f}",
    delta=f"{delta_pct:+.0f}% vs {prev_month_display}"
    if delta_pct is not None
    else f"{prev_month_display} unavailable",
    delta_color="inverse",
)
kpi_2.metric(
    f"Difference vs {prev_month_display}",
    f"{delta_abs:+,.0f}€",
)
kpi_3.metric(
    "YTD spend",
    f"€{current_ytd_spend:,.0f}",
    delta=f"{ytd_delta_pct:+.0f}% vs {previous_year} YTD"
    if ytd_delta_pct is not None
    else f"{previous_year} YTD unavailable",
    delta_color="inverse",
)
kpi_4.metric(
    f"Difference vs {previous_year} YTD",
    f"{ytd_delta_abs:+,.0f}€",
)

st.divider()

team_provider = (
    filtered.groupby(["team", "provider"], as_index=False)["cost_usd"]
    .sum()
    .sort_values(["team", "cost_usd"], ascending=[True, False])
)
team_provider_display = team_provider.copy()
team_provider_display["team"] = team_provider_display["team"].map(team_label)

prev_month_df = with_environment_group(filter_month(df, prev_month))
prev_month_df = prev_month_df[
    prev_month_df["team"].isin(selected_teams)
    & prev_month_df["provider"].isin(selected_providers)
    & prev_month_df["environment_group"].isin(selected_environment_groups)
].copy()

current_team_totals = (
    filtered.groupby("team", as_index=False)["cost_usd"]
    .sum()
    .sort_values("cost_usd", ascending=False)
)
previous_team_totals = prev_month_df.groupby("team", as_index=False)["cost_usd"].sum()
previous_by_team = {
    str(row["team"]): float(row["cost_usd"])
    for _, row in previous_team_totals.iterrows()
}

team_cards_data = [
    {
        "team": team_label(str(row["team"])),
        "current_cost": float(row["cost_usd"]),
        "previous_cost": previous_by_team.get(str(row["team"]), 0.0),
    }
    for _, row in current_team_totals.iterrows()
]

render_vertical_stacked_bar(
    frame=team_provider_display,
    category_col="team",
    series_col="provider",
    value_col="cost_usd",
    title="Cost by team (stacked by provider)",
    height=500,
)

st.divider()
st.subheader(f"Team KPIs (vs {prev_month_display})")
render_team_kpi_cards(
    team_data=team_cards_data,
    previous_period_label=prev_month_display,
    currency_symbol="€",
    max_cards_per_row=4,
)

st.info(
    "For deeper analysis, open the `Team`, `Environment`, or `Providers` pages from the sidebar."
)
