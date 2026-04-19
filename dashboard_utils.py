from __future__ import annotations

import pandas as pd


def _to_month_label(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.strftime("%Y-%m")


def available_months(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []

    months = _to_month_label(df["date"]).drop_duplicates().sort_values(ascending=False)
    return months.tolist()


def filter_month(df: pd.DataFrame, month_label: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    month_series = _to_month_label(df["date"])
    return df.loc[month_series == month_label].copy()


def previous_month_label(month_label: str) -> str:
    current = pd.to_datetime(f"{month_label}-01")
    previous = current - pd.DateOffset(months=1)
    return previous.strftime("%Y-%m")


def month_total_cost(
    df: pd.DataFrame,
    month_label: str,
    teams: list[str] | None = None,
    providers: list[str] | None = None,
    environment_groups: list[str] | None = None,
) -> float:
    month_df = with_environment_group(filter_month(df, month_label))
    if month_df.empty:
        return 0.0

    if teams:
        month_df = month_df[month_df["team"].isin(teams)]
    if providers:
        month_df = month_df[month_df["provider"].isin(providers)]
    if environment_groups:
        month_df = month_df[month_df["environment_group"].isin(environment_groups)]

    return float(month_df["cost_usd"].sum())


def with_environment_group(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        copy = df.copy()
        copy["environment_group"] = []
        return copy

    copy = df.copy()
    copy["environment_group"] = copy["environment"].map(
        lambda env: "prod" if str(env).lower() == "prod" else "non-prod"
    )
    return copy


def team_provider_monthly_cost(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["team", "provider", "cost_usd"])

    grouped = (
        df.groupby(["team", "provider"], as_index=False)["cost_usd"]
        .sum()
        .sort_values(["team", "cost_usd"], ascending=[True, False])
    )
    return grouped
