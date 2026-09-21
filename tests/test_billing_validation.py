"""Each rule in tools/validate_billing_data.py must fire when the data actually breaks."""

import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from validate_billing_data import (  # noqa: E402
    RULES,
    check_schema,
    rule_cost_math,
    rule_costs_non_negative,
    rule_currency_ratio_consistent,
    rule_dates_parse_and_order,
    rule_no_nulls,
    rule_rounding_consistent,
    rule_unique_resource_ids,
    rule_utilization_bounds,
)

DATA = os.path.join(ROOT, "data", "raw", "gcp_final_approved_dataset.csv")


@pytest.fixture(scope="module")
def clean():
    return pd.read_csv(DATA)


def test_real_dataset_passes_every_rule(clean):
    for rule_id, _, _, check in RULES:
        detail, _ = check(clean)
        assert detail is None, f"{rule_id} failed on the real dataset: {detail}"


def test_schema_rule_catches_missing_and_extra_columns(clean):
    assert check_schema(clean.drop(columns=["Usage Unit"]))[0]
    assert check_schema(clean.assign(surprise=1))[0]


def test_null_rule_catches_injected_null(clean):
    df = clean.copy()
    df.loc[0, "Rounded Cost ($)"] = None
    assert "nulls found" in rule_no_nulls(df)[0]


def test_duplicate_resource_id_caught(clean):
    df = pd.concat([clean, clean.head(1)], ignore_index=True)
    assert rule_unique_resource_ids(df)[0]


def test_utilization_out_of_bounds_caught(clean):
    df = clean.copy()
    df.loc[0, "CPU Utilization (%)"] = 150
    df.loc[1, "Memory Utilization (%)"] = -5
    assert rule_utilization_bounds(df)[1] == 2


def test_negative_cost_caught(clean):
    df = clean.copy()
    df.loc[0, "Rounded Cost ($)"] = -10
    assert rule_costs_non_negative(df)[0]


def test_cost_math_mismatch_caught(clean):
    df = clean.copy()
    df.loc[0, "Unrounded Cost ($)"] = df.loc[0, "Unrounded Cost ($)"] + 25
    assert rule_cost_math(df)[0]


def test_rounding_mismatch_caught(clean):
    df = clean.copy()
    df["Rounded Cost ($)"] = df["Rounded Cost ($)"].astype(float)
    df.loc[0, "Rounded Cost ($)"] = df.loc[0, "Unrounded Cost ($)"] + 50
    assert rule_rounding_consistent(df)[0]


def test_bad_and_reversed_dates_caught(clean):
    df = clean.copy()
    df.loc[0, "Usage Start Date"] = "2024/08/01 10:00"
    assert "unparseable" in rule_dates_parse_and_order(df)[0]

    df2 = clean.copy()
    df2.loc[0, "Usage End Date"] = df2.loc[0, "Usage Start Date"]
    df2.loc[0, "Usage Start Date"] = "30-12-2024 23:00"
    assert "ends before it starts" in rule_dates_parse_and_order(df2)[0]


def test_mixed_exchange_rate_caught(clean):
    df = clean.copy()
    df.loc[0, "Total Cost (INR)"] = df.loc[0, "Rounded Cost ($)"] * 200  # different rate
    assert rule_currency_ratio_consistent(df)[0]


def test_rule_ids_unique_and_dimensions_known():
    ids = [r[0] for r in RULES]
    assert len(ids) == len(set(ids))
    assert {r[1] for r in RULES} <= {"schema", "completeness", "uniqueness", "validity", "accuracy", "consistency"}
