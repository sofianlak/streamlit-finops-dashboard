from __future__ import annotations

import calendar
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, Iterable, List

PROVIDERS = ("Azure", "Snowflake", "MongoDB", "Confluent")

SERVICE_CATALOG: Dict[str, List[str]] = {
    "Azure": ["Compute", "Storage", "Networking", "AKS", "Databricks"],
    "Snowflake": ["Warehouse", "Cloud Services", "Storage", "Data Transfer"],
    "MongoDB": ["Atlas Compute", "Atlas Storage", "Data Transfer", "Backup"],
    "Confluent": ["Kafka Cluster", "Connect", "ksqlDB", "Schema Registry"],
}

BASE_DAILY_COST = {
    "Azure": 12500.0,
    "Snowflake": 8600.0,
    "MongoDB": 4100.0,
    "Confluent": 4700.0,
}

DAILY_GROWTH = {
    "Azure": 14.0,
    "Snowflake": 11.0,
    "MongoDB": 5.0,
    "Confluent": 6.5,
}

VOLATILITY = {
    "Azure": 0.09,
    "Snowflake": 0.10,
    "MongoDB": 0.07,
    "Confluent": 0.08,
}

COMMITMENT_TARGET = {
    "Azure": 0.66,
    "Snowflake": 0.42,
    "MongoDB": 0.37,
    "Confluent": 0.53,
}

UNIT_PRICE = {
    "Azure": 0.19,
    "Snowflake": 3.80,
    "MongoDB": 0.48,
    "Confluent": 0.62,
}

ENVIRONMENTS = ("prod", "staging", "dev")
ENV_WEIGHTS = (0.73, 0.18, 0.09)

TEAMS = ("TID", "MB4", "DTU", "QSS", "I2A", "SMW", "SMH", "MNG")
TEAM_WEIGHTS = (0.13, 0.12, 0.13, 0.12, 0.12, 0.12, 0.13, 0.13)

REGIONS = ("westeurope", "northeurope", "eastus", "westus2")
REGION_WEIGHTS = (0.36, 0.24, 0.23, 0.17)


def _date_range(start_date: date, end_date: date) -> Iterable[date]:
    day_count = (end_date - start_date).days + 1
    for offset in range(day_count):
        yield start_date + timedelta(days=offset)


def _weighted_pick(rng: random.Random, values: Iterable[str], weights: Iterable[float]) -> str:
    values_list = list(values)
    weights_list = list(weights)
    return rng.choices(values_list, weights=weights_list, k=1)[0]


def _normalized_weights(count: int, rng: random.Random) -> List[float]:
    raw = [max(0.02, 1.0 + rng.uniform(-0.20, 0.20)) for _ in range(count)]
    total = sum(raw)
    return [value / total for value in raw]


def generate_finops_records(start_date: date, end_date: date, seed: int = 7) -> List[dict]:
    if end_date < start_date:
        raise ValueError("end_date must be greater than or equal to start_date")

    rng = random.Random(seed)
    records: List[dict] = []

    for day_index, current_date in enumerate(_date_range(start_date, end_date)):
        weekly_cycle = 1.0 + 0.08 * math.sin(2 * math.pi * day_index / 7)

        for provider in PROVIDERS:
            baseline = BASE_DAILY_COST[provider] + DAILY_GROWTH[provider] * day_index
            noise = 1.0 + rng.uniform(-VOLATILITY[provider], VOLATILITY[provider])
            provider_daily_cost = max(600.0, baseline * weekly_cycle * noise)

            services = SERVICE_CATALOG[provider]
            service_weights = _normalized_weights(len(services), rng)

            for service, share in zip(services, service_weights):
                service_cost = provider_daily_cost * share
                commitment_coverage = min(
                    0.95,
                    max(0.10, COMMITMENT_TARGET[provider] + rng.uniform(-0.10, 0.10)),
                )
                waste_pct = min(
                    0.40,
                    max(0.02, 0.05 + (1.0 - commitment_coverage) * 0.25 + rng.uniform(-0.03, 0.03)),
                )

                usage_units = max(
                    1.0,
                    (service_cost / UNIT_PRICE[provider]) * rng.uniform(0.93, 1.07),
                )

                records.append(
                    {
                        "date": current_date,
                        "provider": provider,
                        "service": service,
                        "environment": _weighted_pick(rng, ENVIRONMENTS, ENV_WEIGHTS),
                        "team": _weighted_pick(rng, TEAMS, TEAM_WEIGHTS),
                        "region": _weighted_pick(rng, REGIONS, REGION_WEIGHTS),
                        "cost_usd": float(service_cost),
                        "usage_units": float(usage_units),
                        "waste_pct": float(waste_pct),
                        "commitment_coverage": float(commitment_coverage),
                    }
                )

    return records


def _filter_records(
    records: Iterable[dict],
    providers: Iterable[str] | None = None,
    environments: Iterable[str] | None = None,
) -> List[dict]:
    provider_filter = set(providers) if providers else None
    environment_filter = set(environments) if environments else None

    filtered: List[dict] = []
    for record in records:
        if provider_filter and record["provider"] not in provider_filter:
            continue
        if environment_filter and record["environment"] not in environment_filter:
            continue
        filtered.append(record)

    return filtered


def total_cost(
    records: Iterable[dict],
    providers: Iterable[str] | None = None,
    environments: Iterable[str] | None = None,
) -> float:
    filtered = _filter_records(records, providers=providers, environments=environments)
    return float(sum(record["cost_usd"] for record in filtered))


def estimate_month_end_cost(
    records: Iterable[dict],
    month: int,
    year: int,
    providers: Iterable[str] | None = None,
    environments: Iterable[str] | None = None,
) -> float:
    filtered = _filter_records(records, providers=providers, environments=environments)
    month_records = [
        record
        for record in filtered
        if record["date"].year == year and record["date"].month == month
    ]

    if not month_records:
        return 0.0

    daily_cost: Dict[date, float] = defaultdict(float)
    for record in month_records:
        daily_cost[record["date"]] += float(record["cost_usd"])

    observed_days = sorted(daily_cost)
    current_total = sum(daily_cost.values())
    day_count = len(observed_days)
    days_in_month = calendar.monthrange(year, month)[1]

    if day_count == 0:
        return 0.0

    average = current_total / day_count
    if day_count >= 7:
        trailing_days = observed_days[-7:]
        trailing_avg = sum(daily_cost[d] for d in trailing_days) / 7
        projected_daily = max(0.0, average * 0.65 + trailing_avg * 0.35)
    else:
        projected_daily = max(0.0, average)

    remaining_days = max(0, days_in_month - observed_days[-1].day)
    forecast = current_total + projected_daily * remaining_days

    return float(forecast)


def top_savings_opportunities(records: Iterable[dict], limit: int = 8) -> List[dict]:
    grouped: Dict[tuple, dict] = {}

    for record in records:
        key = (record["provider"], record["service"], record["environment"])
        if key not in grouped:
            grouped[key] = {
                "provider": record["provider"],
                "service": record["service"],
                "environment": record["environment"],
                "cost_usd": 0.0,
                "potential_savings_usd": 0.0,
            }

        grouped_row = grouped[key]
        grouped_row["cost_usd"] += float(record["cost_usd"])
        grouped_row["potential_savings_usd"] += float(record["cost_usd"]) * float(record["waste_pct"]) * 0.60

    opportunities = sorted(
        grouped.values(),
        key=lambda row: row["potential_savings_usd"],
        reverse=True,
    )

    return opportunities[:limit]


def detect_spikes(records: Iterable[dict], z_threshold: float = 2.6) -> List[dict]:
    per_provider_day: Dict[str, Dict[date, float]] = defaultdict(lambda: defaultdict(float))

    for record in records:
        per_provider_day[record["provider"]][record["date"]] += float(record["cost_usd"])

    spikes: List[dict] = []

    for provider, day_totals in per_provider_day.items():
        values = list(day_totals.values())
        if len(values) < 3:
            continue

        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        std_dev = math.sqrt(variance)
        if std_dev == 0:
            continue

        for day, value in day_totals.items():
            z_score = (value - mean) / std_dev
            if z_score >= z_threshold:
                spikes.append(
                    {
                        "provider": provider,
                        "date": day,
                        "daily_cost_usd": float(value),
                        "z_score": float(z_score),
                    }
                )

    spikes.sort(key=lambda row: row["z_score"], reverse=True)
    return spikes
