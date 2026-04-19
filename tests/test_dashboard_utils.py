from datetime import date
import unittest

import pandas as pd

from dashboard_utils import (
    available_months,
    filter_month,
    month_total_cost,
    previous_month_label,
    team_provider_monthly_cost,
    with_environment_group,
)


class DashboardUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame(
            [
                {"date": date(2026, 1, 2), "team": "Core", "provider": "Azure", "environment": "prod", "cost_usd": 100.0},
                {"date": date(2026, 1, 15), "team": "Data", "provider": "Snowflake", "environment": "staging", "cost_usd": 120.0},
                {"date": date(2026, 2, 1), "team": "Core", "provider": "Azure", "environment": "prod", "cost_usd": 130.0},
                {"date": date(2026, 2, 11), "team": "Payments", "provider": "Confluent", "environment": "dev", "cost_usd": 90.0},
                {"date": date(2026, 3, 3), "team": "Data", "provider": "MongoDB", "environment": "prod", "cost_usd": 80.0},
            ]
        )

    def test_available_months_returns_desc_unique(self) -> None:
        months = available_months(self.df)
        self.assertEqual(months, ["2026-03", "2026-02", "2026-01"])

    def test_filter_month_filters_exact_month(self) -> None:
        filtered = filter_month(self.df, "2026-02")
        self.assertEqual(len(filtered), 2)
        self.assertTrue((filtered["date"].apply(lambda d: d.month) == 2).all())

    def test_team_provider_monthly_cost_groups_and_sorts(self) -> None:
        feb = filter_month(self.df, "2026-02")
        grouped = team_provider_monthly_cost(feb)
        self.assertEqual(list(grouped.columns), ["team", "provider", "cost_usd"])
        self.assertEqual(float(grouped["cost_usd"].sum()), 220.0)

    def test_previous_month_label_handles_year_boundary(self) -> None:
        self.assertEqual(previous_month_label("2026-01"), "2025-12")
        self.assertEqual(previous_month_label("2026-03"), "2026-02")

    def test_month_total_cost_respects_filters(self) -> None:
        feb_total = month_total_cost(self.df, "2026-02")
        self.assertEqual(feb_total, 220.0)

        feb_core_only = month_total_cost(self.df, "2026-02", teams=["Core"])
        self.assertEqual(feb_core_only, 130.0)

        feb_azure_only = month_total_cost(self.df, "2026-02", providers=["Azure"])
        self.assertEqual(feb_azure_only, 130.0)

        feb_non_prod_only = month_total_cost(self.df, "2026-02", environment_groups=["non-prod"])
        self.assertEqual(feb_non_prod_only, 90.0)

    def test_with_environment_group_maps_prod_vs_non_prod(self) -> None:
        enriched = with_environment_group(self.df)
        mapping = dict(zip(enriched["environment"], enriched["environment_group"]))
        self.assertEqual(mapping["prod"], "prod")
        self.assertEqual(mapping["staging"], "non-prod")
        self.assertEqual(mapping["dev"], "non-prod")


if __name__ == "__main__":
    unittest.main()
