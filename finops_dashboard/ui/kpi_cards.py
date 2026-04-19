from __future__ import annotations

from typing import Mapping, Sequence

import streamlit as st


def _format_money(value: float, currency_symbol: str = "€") -> str:
    return f"{currency_symbol}{value:,.0f}"


def _mom_change_pct(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100.0


def _chunk(items: Sequence[Mapping[str, float | str]], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def render_team_kpi_cards(
    team_data: Sequence[Mapping[str, float | str]],
    previous_period_label: str,
    currency_symbol: str = "€",
    max_cards_per_row: int = 4,
) -> None:
    if not team_data:
        st.info("No teams to display.")
        return

    cards_per_row = max(1, max_cards_per_row)

    for row_items in _chunk(list(team_data), cards_per_row):
        cols = st.columns(len(row_items), gap="medium")
        for col, item in zip(cols, row_items):
            team = str(item["team"])
            current_cost = float(item["current_cost"])
            previous_cost = float(item["previous_cost"])
            delta_amount = current_cost - previous_cost

            change = _mom_change_pct(current_cost, previous_cost)
            if change is None:
                change_text = "N/A"
                change_color = "gray"
                change_help = f"{previous_period_label}: {_format_money(previous_cost, currency_symbol)}"
                delta_text = "N/A"
            elif change > 0:
                change_text = f"↑ +{change:.0f}%"
                change_color = "red"
                change_help = f"{previous_period_label}: {_format_money(previous_cost, currency_symbol)}"
                delta_text = f"+{_format_money(delta_amount, currency_symbol)}"
            elif change < 0:
                change_text = f"↓ {change:.0f}%"
                change_color = "green"
                change_help = f"{previous_period_label}: {_format_money(previous_cost, currency_symbol)}"
                delta_text = f"-{_format_money(abs(delta_amount), currency_symbol)}"
            else:
                change_text = "→ 0%"
                change_color = "gray"
                change_help = f"{previous_period_label}: {_format_money(previous_cost, currency_symbol)}"
                delta_text = _format_money(0, currency_symbol)

            with col:
                with st.container(border=True):
                    st.markdown(f"**{team}**")
                    st.markdown(f"#### {_format_money(current_cost, currency_symbol)}")
                    trend_cols = st.columns([2, 1], gap="small")
                    with trend_cols[0]:
                        st.badge(change_text, icon=None, color=change_color, help=change_help)
                    with trend_cols[1]:
                        st.markdown(f":{change_color}[{delta_text}]")
