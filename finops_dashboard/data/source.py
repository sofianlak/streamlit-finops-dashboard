from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from finops_dashboard.config.team_labels import team_label
from finops_dashboard.data.model import generate_finops_records
from finops_dashboard.data.transforms import available_months, filter_month, with_environment_group


HISTORY_DAYS = 540
SIMULATION_SEED = 23
ENVIRONMENT_GROUPS = ("prod", "non-prod")


@st.cache_data(show_spinner=False)
def load_records() -> pd.DataFrame:
    end_date = date.today()
    start_date = end_date - timedelta(days=HISTORY_DAYS - 1)
    records = generate_finops_records(
        start_date=start_date,
        end_date=end_date,
        seed=SIMULATION_SEED,
    )
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


def format_month_label(month_label: str) -> str:
    as_date = pd.to_datetime(f"{month_label}-01")
    return as_date.strftime("%B %Y").capitalize()


def select_filters(
    df: pd.DataFrame,
    key_prefix: str,
) -> tuple[str, pd.DataFrame, list[str], list[str], list[str]]:
    months = available_months(df)
    if not months:
        st.warning("No data available.")
        st.stop()

    st.sidebar.header("Filters")
    selected_month = st.sidebar.selectbox(
        "Month",
        options=months,
        index=0,
        key=f"{key_prefix}_month",
    )

    month_df = with_environment_group(filter_month(df, selected_month))
    if month_df.empty:
        st.warning("No data for the selected month.")
        st.stop()

    teams = sorted(month_df["team"].unique().tolist())
    providers = sorted(month_df["provider"].unique().tolist())

    selected_teams = st.sidebar.multiselect(
        "Teams",
        options=teams,
        default=teams,
        key=f"{key_prefix}_teams",
        format_func=team_label,
    )
    selected_providers = st.sidebar.multiselect(
        "Providers",
        options=providers,
        default=providers,
        key=f"{key_prefix}_providers",
    )
    selected_environment_groups = st.sidebar.multiselect(
        "Environment",
        options=list(ENVIRONMENT_GROUPS),
        default=list(ENVIRONMENT_GROUPS),
        key=f"{key_prefix}_env",
    )

    if not selected_teams:
        st.warning("Select at least one team.")
        st.stop()
    if not selected_providers:
        st.warning("Select at least one provider.")
        st.stop()
    if not selected_environment_groups:
        st.warning("Select at least one environment.")
        st.stop()

    filtered = month_df[
        month_df["team"].isin(selected_teams)
        & month_df["provider"].isin(selected_providers)
        & month_df["environment_group"].isin(selected_environment_groups)
    ].copy()

    if filtered.empty:
        st.warning("No data with these filters.")
        st.stop()

    return (
        selected_month,
        filtered,
        selected_teams,
        selected_providers,
        selected_environment_groups,
    )
