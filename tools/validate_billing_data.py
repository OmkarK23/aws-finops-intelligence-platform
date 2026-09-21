"""
Data quality checks for the cloud billing dataset before it is analyzed.

Cost analysis is only as trustworthy as the billing data underneath it, so these rules
run against the raw CSV and report what fails, per rule, with example rows.

Usage:
    python tools/validate_billing_data.py
    python tools/validate_billing_data.py --input data/raw/gcp_final_approved_dataset.csv --fail-on-error
"""

import argparse
import sys

import pandas as pd

REQUIRED_COLUMNS = [
    "Resource ID", "Service Name", "Usage Quantity", "Usage Unit", "Region/Zone",
    "CPU Utilization (%)", "Memory Utilization (%)",
    "Network Inbound Data (Bytes)", "Network Outbound Data (Bytes)",
    "Usage Start Date", "Usage End Date",
    "Cost per Quantity ($)", "Unrounded Cost ($)", "Rounded Cost ($)", "Total Cost (INR)",
]

DATE_FORMAT = "%d-%m-%Y %H:%M"
ROUNDING_TOLERANCE = 1.0   # Rounded Cost should be within 1 USD of Unrounded Cost
COST_TOLERANCE = 0.01      # quantity * unit price should match unrounded cost within 1 cent


def check_schema(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    details = []
    if missing:
        details.append(f"missing columns: {missing}")
    if extra:
        details.append(f"unexpected columns: {extra}")
    return None if not details else "; ".join(details), 0


def rule_no_nulls(df):
    counts = df[[c for c in REQUIRED_COLUMNS if c in df.columns]].isna().sum()
    bad = counts[counts > 0]
    return (f"nulls found: {bad.to_dict()}" if len(bad) else None), int(bad.sum())


def rule_unique_resource_ids(df):
    dupes = df["Resource ID"].duplicated().sum()
    return (f"{dupes} duplicate Resource ID values" if dupes else None), int(dupes)


def rule_utilization_bounds(df):
    mask = ~df["CPU Utilization (%)"].between(0, 100) | ~df["Memory Utilization (%)"].between(0, 100)
    return (f"{mask.sum()} rows with utilization outside 0-100" if mask.any() else None), int(mask.sum())


def rule_costs_non_negative(df):
    mask = (df["Rounded Cost ($)"] < 0) | (df["Unrounded Cost ($)"] < 0) | (df["Usage Quantity"] < 0)
    return (f"{mask.sum()} rows with negative cost or usage" if mask.any() else None), int(mask.sum())


def rule_cost_math(df):
    expected = df["Usage Quantity"] * df["Cost per Quantity ($)"]
    mask = (expected - df["Unrounded Cost ($)"]).abs() > COST_TOLERANCE
    return (f"{mask.sum()} rows where quantity x unit price does not match unrounded cost" if mask.any() else None), int(mask.sum())


def rule_rounding_consistent(df):
    mask = (df["Rounded Cost ($)"] - df["Unrounded Cost ($)"]).abs() > ROUNDING_TOLERANCE
    return (f"{mask.sum()} rows where rounded and unrounded cost differ by more than ${ROUNDING_TOLERANCE}" if mask.any() else None), int(mask.sum())


def rule_dates_parse_and_order(df):
    start = pd.to_datetime(df["Usage Start Date"], format=DATE_FORMAT, errors="coerce")
    end = pd.to_datetime(df["Usage End Date"], format=DATE_FORMAT, errors="coerce")
    unparsed = int(start.isna().sum() + end.isna().sum())
    out_of_order = int((end < start).sum())
    details = []
    if unparsed:
        details.append(f"{unparsed} unparseable dates")
    if out_of_order:
        details.append(f"{out_of_order} rows where usage ends before it starts")
    return ("; ".join(details) if details else None), unparsed + out_of_order


def rule_currency_ratio_consistent(df):
    """Total Cost (INR) should be the USD cost times one exchange rate, the same rate for every row."""
    ratio = df["Total Cost (INR)"] / df["Rounded Cost ($)"].replace(0, pd.NA)
    spread = ratio.max() - ratio.min()
    if spread > 0.5:
        return (f"INR/USD ratio is not constant: ranges {ratio.min():.2f} to {ratio.max():.2f}, "
                f"so the INR column mixes exchange rates"), int(len(df))
    return None, 0


RULES = [
    ("BQ-01", "schema", "File has exactly the expected columns", check_schema),
    ("BQ-02", "completeness", "No nulls in any required column", rule_no_nulls),
    ("BQ-03", "uniqueness", "Resource ID is unique per row", rule_unique_resource_ids),
    ("BQ-04", "validity", "CPU and memory utilization are between 0 and 100", rule_utilization_bounds),
    ("BQ-05", "validity", "Costs and usage quantities are not negative", rule_costs_non_negative),
    ("BQ-06", "accuracy", "Usage quantity x unit price equals unrounded cost", rule_cost_math),
    ("BQ-07", "consistency", "Rounded cost is within $1 of unrounded cost", rule_rounding_consistent),
    ("BQ-08", "validity", "Usage dates parse and end is not before start", rule_dates_parse_and_order),
    ("BQ-09", "consistency", "INR column uses a single exchange rate", rule_currency_ratio_consistent),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/gcp_final_approved_dataset.csv")
    parser.add_argument("--fail-on-error", action="store_true",
                        help="exit 1 if any rule fails, so this can gate a pipeline run")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    print(f"Validating {args.input}: {len(df):,} rows, {len(df.columns)} columns\n")

    failures = 0
    for rule_id, dimension, description, check in RULES:
        detail, count = check(df)
        status = "PASS" if detail is None else "FAIL"
        if detail is not None:
            failures += 1
        print(f"{status}  {rule_id} [{dimension}] {description}")
        if detail:
            print(f"        {detail}")

    print(f"\n{len(RULES) - failures} of {len(RULES)} rules passed.")
    if failures and args.fail_on_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
