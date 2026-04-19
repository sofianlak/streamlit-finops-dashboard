from datetime import date
import unittest

from finops_model import (
    PROVIDERS,
    TEAMS,
    detect_spikes,
    estimate_month_end_cost,
    generate_finops_records,
    top_savings_opportunities,
    total_cost,
)


class FinopsModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = generate_finops_records(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            seed=13,
        )

    def test_generates_expected_providers(self) -> None:
        providers = {record["provider"] for record in self.records}
        self.assertEqual(providers, set(PROVIDERS))

    def test_teams_match_expected_business_units(self) -> None:
        self.assertEqual(
            TEAMS,
            ("TID", "MB4", "DTU", "QSS", "I2A", "SMW", "SMH", "MNG"),
        )

    def test_generated_metrics_are_positive(self) -> None:
        for record in self.records:
            self.assertGreater(record["cost_usd"], 0)
            self.assertGreater(record["usage_units"], 0)
            self.assertGreaterEqual(record["waste_pct"], 0)
            self.assertLessEqual(record["waste_pct"], 0.40)

    def test_total_cost_matches_manual_sum(self) -> None:
        manual_sum = sum(record["cost_usd"] for record in self.records)
        self.assertAlmostEqual(total_cost(self.records), manual_sum, places=6)

    def test_month_end_forecast_not_below_current_spend(self) -> None:
        partial_records = generate_finops_records(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 15),
            seed=21,
        )
        forecast = estimate_month_end_cost(partial_records, month=2, year=2026)
        self.assertGreaterEqual(forecast, total_cost(partial_records))

    def test_top_savings_sorted_desc(self) -> None:
        opportunities = top_savings_opportunities(self.records, limit=7)
        self.assertLessEqual(len(opportunities), 7)
        if len(opportunities) >= 2:
            self.assertGreaterEqual(
                opportunities[0]["potential_savings_usd"],
                opportunities[1]["potential_savings_usd"],
            )

    def test_detect_spikes_flags_outlier(self) -> None:
        baseline = [
            {
                "date": date(2026, 3, day),
                "provider": "Azure",
                "service": "Compute",
                "environment": "prod",
                "team": "Core",
                "region": "westeurope",
                "cost_usd": 100.0,
                "usage_units": 100.0,
                "waste_pct": 0.10,
                "commitment_coverage": 0.60,
            }
            for day in range(1, 11)
        ]
        baseline.append(
            {
                "date": date(2026, 3, 11),
                "provider": "Azure",
                "service": "Compute",
                "environment": "prod",
                "team": "Core",
                "region": "westeurope",
                "cost_usd": 600.0,
                "usage_units": 100.0,
                "waste_pct": 0.10,
                "commitment_coverage": 0.60,
            }
        )

        spikes = detect_spikes(baseline, z_threshold=2.0)
        spike_days = {row["date"] for row in spikes}
        self.assertIn(date(2026, 3, 11), spike_days)


if __name__ == "__main__":
    unittest.main()
