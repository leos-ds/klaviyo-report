"""Industry benchmarks for Klaviyo flow performance grading.

Source: Klaviyo Industry Benchmark Report 2025, Omnisend benchmarks 2025,
plus Digismoothie pilot data (Krekry.cz May 2026).

`good` = the threshold above which the flow is performing well
`warn` = below `warn` is RED, between warn and good is YELLOW
"""
from __future__ import annotations


# Benchmarks per flow category, per industry.
# Falls back to "default" when industry not found.

BENCHMARKS: dict[str, dict[str, dict[str, dict[str, float]]]] = {
    "food_beverage": {
        "welcome":          {"open": {"good": 0.35, "warn": 0.25}, "ctr": {"good": 0.05, "warn": 0.03}, "conv": {"good": 0.04, "warn": 0.02}},
        "cart_abandon":     {"open": {"good": 0.40, "warn": 0.30}, "ctr": {"good": 0.06, "warn": 0.04}, "conv": {"good": 0.03, "warn": 0.015}},
        "checkout_abandon": {"open": {"good": 0.45, "warn": 0.35}, "ctr": {"good": 0.08, "warn": 0.05}, "conv": {"good": 0.04, "warn": 0.02}},
        "post_purchase":    {"open": {"good": 0.40, "warn": 0.30}, "ctr": {"good": 0.06, "warn": 0.03}, "conv": {"good": 0.01, "warn": 0.005}},
        "browse_abandon":   {"open": {"good": 0.35, "warn": 0.25}, "ctr": {"good": 0.04, "warn": 0.025}, "conv": {"good": 0.015, "warn": 0.008}},
        "sunset":           {"open": {"good": 0.05, "warn": 0.02}, "ctr": {"good": 0.005, "warn": 0.002}, "conv": {"good": 0.001, "warn": 0.0005}},
        "winback":          {"open": {"good": 0.20, "warn": 0.12}, "ctr": {"good": 0.025, "warn": 0.012}, "conv": {"good": 0.01, "warn": 0.005}},
        "default":          {"open": {"good": 0.25, "warn": 0.15}, "ctr": {"good": 0.03, "warn": 0.015}, "conv": {"good": 0.015, "warn": 0.008}},
    },
    "fashion": {
        "welcome":          {"open": {"good": 0.30, "warn": 0.22}, "ctr": {"good": 0.04, "warn": 0.025}, "conv": {"good": 0.03, "warn": 0.015}},
        "cart_abandon":     {"open": {"good": 0.38, "warn": 0.28}, "ctr": {"good": 0.05, "warn": 0.035}, "conv": {"good": 0.025, "warn": 0.012}},
        "checkout_abandon": {"open": {"good": 0.42, "warn": 0.32}, "ctr": {"good": 0.06, "warn": 0.04}, "conv": {"good": 0.03, "warn": 0.015}},
        "post_purchase":    {"open": {"good": 0.38, "warn": 0.28}, "ctr": {"good": 0.05, "warn": 0.025}, "conv": {"good": 0.008, "warn": 0.004}},
        "browse_abandon":   {"open": {"good": 0.32, "warn": 0.22}, "ctr": {"good": 0.035, "warn": 0.02}, "conv": {"good": 0.012, "warn": 0.006}},
        "sunset":           {"open": {"good": 0.05, "warn": 0.02}, "ctr": {"good": 0.005, "warn": 0.002}, "conv": {"good": 0.001, "warn": 0.0005}},
        "winback":          {"open": {"good": 0.18, "warn": 0.10}, "ctr": {"good": 0.022, "warn": 0.01}, "conv": {"good": 0.008, "warn": 0.004}},
        "default":          {"open": {"good": 0.22, "warn": 0.14}, "ctr": {"good": 0.028, "warn": 0.014}, "conv": {"good": 0.012, "warn": 0.006}},
    },
    "sports_outdoor": {
        "welcome":          {"open": {"good": 0.32, "warn": 0.22}, "ctr": {"good": 0.045, "warn": 0.028}, "conv": {"good": 0.035, "warn": 0.018}},
        "cart_abandon":     {"open": {"good": 0.38, "warn": 0.28}, "ctr": {"good": 0.055, "warn": 0.035}, "conv": {"good": 0.028, "warn": 0.014}},
        "checkout_abandon": {"open": {"good": 0.42, "warn": 0.32}, "ctr": {"good": 0.07, "warn": 0.045}, "conv": {"good": 0.035, "warn": 0.018}},
        "post_purchase":    {"open": {"good": 0.38, "warn": 0.28}, "ctr": {"good": 0.05, "warn": 0.025}, "conv": {"good": 0.008, "warn": 0.004}},
        "browse_abandon":   {"open": {"good": 0.32, "warn": 0.22}, "ctr": {"good": 0.035, "warn": 0.02}, "conv": {"good": 0.012, "warn": 0.006}},
        "sunset":           {"open": {"good": 0.05, "warn": 0.02}, "ctr": {"good": 0.005, "warn": 0.002}, "conv": {"good": 0.001, "warn": 0.0005}},
        "winback":          {"open": {"good": 0.18, "warn": 0.10}, "ctr": {"good": 0.022, "warn": 0.01}, "conv": {"good": 0.008, "warn": 0.004}},
        "default":          {"open": {"good": 0.24, "warn": 0.15}, "ctr": {"good": 0.03, "warn": 0.015}, "conv": {"good": 0.013, "warn": 0.007}},
    },
    "lifestyle": {
        "welcome":          {"open": {"good": 0.30, "warn": 0.22}, "ctr": {"good": 0.04, "warn": 0.025}, "conv": {"good": 0.028, "warn": 0.014}},
        "cart_abandon":     {"open": {"good": 0.36, "warn": 0.26}, "ctr": {"good": 0.05, "warn": 0.03}, "conv": {"good": 0.022, "warn": 0.011}},
        "checkout_abandon": {"open": {"good": 0.40, "warn": 0.30}, "ctr": {"good": 0.06, "warn": 0.04}, "conv": {"good": 0.028, "warn": 0.014}},
        "post_purchase":    {"open": {"good": 0.36, "warn": 0.26}, "ctr": {"good": 0.045, "warn": 0.022}, "conv": {"good": 0.007, "warn": 0.003}},
        "browse_abandon":   {"open": {"good": 0.30, "warn": 0.20}, "ctr": {"good": 0.032, "warn": 0.018}, "conv": {"good": 0.010, "warn": 0.005}},
        "sunset":           {"open": {"good": 0.05, "warn": 0.02}, "ctr": {"good": 0.005, "warn": 0.002}, "conv": {"good": 0.001, "warn": 0.0005}},
        "winback":          {"open": {"good": 0.16, "warn": 0.09}, "ctr": {"good": 0.02, "warn": 0.009}, "conv": {"good": 0.007, "warn": 0.003}},
        "default":          {"open": {"good": 0.22, "warn": 0.14}, "ctr": {"good": 0.026, "warn": 0.013}, "conv": {"good": 0.011, "warn": 0.005}},
    },
    "default": {
        "welcome":          {"open": {"good": 0.30, "warn": 0.20}, "ctr": {"good": 0.04, "warn": 0.025}, "conv": {"good": 0.03, "warn": 0.015}},
        "cart_abandon":     {"open": {"good": 0.36, "warn": 0.26}, "ctr": {"good": 0.05, "warn": 0.03}, "conv": {"good": 0.025, "warn": 0.012}},
        "checkout_abandon": {"open": {"good": 0.40, "warn": 0.30}, "ctr": {"good": 0.06, "warn": 0.04}, "conv": {"good": 0.03, "warn": 0.015}},
        "post_purchase":    {"open": {"good": 0.36, "warn": 0.26}, "ctr": {"good": 0.045, "warn": 0.022}, "conv": {"good": 0.008, "warn": 0.004}},
        "browse_abandon":   {"open": {"good": 0.30, "warn": 0.20}, "ctr": {"good": 0.035, "warn": 0.018}, "conv": {"good": 0.012, "warn": 0.006}},
        "sunset":           {"open": {"good": 0.05, "warn": 0.02}, "ctr": {"good": 0.005, "warn": 0.002}, "conv": {"good": 0.001, "warn": 0.0005}},
        "winback":          {"open": {"good": 0.18, "warn": 0.10}, "ctr": {"good": 0.022, "warn": 0.01}, "conv": {"good": 0.008, "warn": 0.004}},
        "default":          {"open": {"good": 0.22, "warn": 0.14}, "ctr": {"good": 0.026, "warn": 0.013}, "conv": {"good": 0.011, "warn": 0.005}},
    },
}


def flow_category(name: str) -> str:
    """Classify a flow by name."""
    n = (name or "").lower()
    if "welcome" in n: return "welcome"
    if "checkout" in n: return "checkout_abandon"
    if "cart" in n: return "cart_abandon"
    if "post-purchase" in n or "post purchase" in n or "postpurchase" in n: return "post_purchase"
    if "browse" in n: return "browse_abandon"
    if "sunset" in n: return "sunset"
    if "winback" in n or "win-back" in n: return "winback"
    return "default"


def grade(metric: str, value: float | None, category: str, industry: str = "default") -> str:
    """Return one of: 'good', 'warn', 'bad', 'neutral'."""
    if value is None:
        return "neutral"
    ind = BENCHMARKS.get(industry, BENCHMARKS["default"])
    cat = ind.get(category, ind["default"])
    t = cat.get(metric)
    if not t:
        return "neutral"
    if value >= t["good"]:
        return "good"
    if value >= t["warn"]:
        return "warn"
    return "bad"


def benchmark_open(category: str, industry: str = "default") -> float:
    """Return the 'good' threshold for open rate."""
    ind = BENCHMARKS.get(industry, BENCHMARKS["default"])
    cat = ind.get(category, ind["default"])
    return cat["open"]["good"]
