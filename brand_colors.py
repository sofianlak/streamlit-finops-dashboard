from __future__ import annotations

PROVIDER_COLORS = {
    "Azure": "#0078D3",
    "Snowflake": "#29B5E8",
    "MongoDB": "#3FA037",
    "Confluent": "#173361",
}

_DEFAULT_COLORS = [
    "#5470C6",
    "#91CC75",
    "#FAC858",
    "#EE6666",
    "#73C0DE",
    "#3BA272",
    "#FC8452",
    "#9A60B4",
    "#EA7CCC",
]


def provider_color_sequence(labels: list[str]) -> list[str]:
    sequence: list[str] = []
    fallback_index = 0

    for label in labels:
        if label in PROVIDER_COLORS:
            sequence.append(PROVIDER_COLORS[label])
            continue

        sequence.append(_DEFAULT_COLORS[fallback_index % len(_DEFAULT_COLORS)])
        fallback_index += 1

    return sequence
