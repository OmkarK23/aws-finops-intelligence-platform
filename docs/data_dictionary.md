# Data Dictionary

Every field this platform reads or produces, what it means, and the rule that keeps it trustworthy. Field profiles below come from the actual dataset in `data/raw/` (1,000 rows, 15 columns).

## Classification

Cloud billing data holds no personal information, but it is commercially sensitive: it exposes infrastructure footprint, spend levels, and where a company is over-provisioned.

| Level | Meaning | Applies to |
|---|---|---|
| **Confidential** | Would reveal cost position or infrastructure layout if shared outside the company | Spend columns, resource inventory, region distribution |
| **Internal** | Operational detail, low sensitivity on its own | Usage units, utilization percentages |

No PII or PHI is present, so no privacy regulation applies to this dataset. The controls that matter here are access control and accuracy, not de-identification.

## Source: raw billing export (`data/raw/*.csv`)

| Column | Type | Definition | Observed range or values | Classification |
|---|---|---|---|---|
| `Resource ID` | string | Unique identifier of the billed resource | 1,000 unique values, format `res-XXXXXXXX` | Confidential |
| `Service Name` | string | Cloud service that generated the charge | 25 distinct services | Confidential |
| `Usage Quantity` | float | Units consumed during the period | 10.54 to 998.01 | Internal |
| `Usage Unit` | string | Unit the quantity is measured in | 3 distinct units | Internal |
| `Region/Zone` | string | Region or zone the resource ran in | 12 distinct regions | Confidential |
| `CPU Utilization (%)` | float | Average CPU used over the period | 0.05 to 99.97 | Internal |
| `Memory Utilization (%)` | float | Average memory used over the period | 0.06 to 99.81 | Internal |
| `Network Inbound Data (Bytes)` | integer | Bytes received | 1.00e9 to 9.98e10 | Internal |
| `Network Outbound Data (Bytes)` | integer | Bytes sent | 1.21e9 to 1.09e11 | Internal |
| `Usage Start Date` | string | Start of the usage period, `DD-MM-YYYY HH:MM` | 2024-06-30 onward | Internal |
| `Usage End Date` | string | End of the usage period, same format | through 2024-09-03 | Internal |
| `Cost per Quantity ($)` | float | Unit price in USD | 1.00 to 9.99 | Confidential |
| `Unrounded Cost ($)` | float | Usage quantity times unit price | 13.91 to 9,003.65 | Confidential |
| `Rounded Cost ($)` | integer | Billed cost in USD, rounded | 14 to 9,004 | Confidential |
| `Total Cost (INR)` | integer | Same cost converted to INR at a single fixed rate | 1,162 to 747,332 | Confidential |

Dataset totals: **$2,135,215** in spend across **1,000 resources**, **61 distinct usage days** (2024-06-30 to 2024-09-03).

`Rounded Cost ($)` is the column every downstream view uses. `Total Cost (INR)` is informational and is not used in analysis.

## Catalog table (`finops_database.gcp_cloud_billing`)

The Glue crawler registers the processed Parquet dataset under snake_case column names. The views reference these:

`resource_id`, `service_name`, `region_zone`, `cpu_utilization_percent`, `memory_utilization_percent`, `rounded_cost_usd`, `usage_start_date`, `usage_end_date`

## Athena views (`sql/finops_views.sql`)

These views are where the business logic lives, so every consumer gets the same definitions instead of each dashboard inventing its own.

| View | Grain | Definition |
|---|---|---|
| `vw_service_spend` | One row per service | Total cost, distinct resource count, average CPU and memory utilization |
| `vw_region_spend` | One row per region or zone | Total cost, distinct resource count, average CPU utilization |
| `vw_underutilized_resources` | One row per resource | Resources running under 20% CPU, with their cost |
| `vw_optimization_recommendations` | One row per resource | A recommendation label and an estimated saving |

### Agreed definitions

These thresholds are the shared vocabulary of the platform. Changing one changes every reported number, so they belong to the cost owner, not to whoever is editing a dashboard.

| Term | Definition |
|---|---|
| **Underutilized** | CPU utilization below 20% |
| **High Risk, terminate or downsize** | CPU below 10% **and** memory below 25%; estimated saving is 70% of the resource cost |
| **Medium Risk, rightsize** | CPU below 20%; estimated saving is 40% of the resource cost |
| **Low Risk, review memory** | Memory below 30%; estimated saving is 20% of the resource cost |
| **Healthy** | Everything else; estimated saving is 0 |
| **Potential waste** | Total cost of all resources under 20% CPU. Currently $420,753 across 193 resources |
| **Estimated savings** | Sum of per-resource savings from the rules above. Currently $278,609 |

The savings percentages are planning heuristics, not vendor-quoted numbers. A real FinOps program would replace them with rightsizing estimates from the cloud provider's own recommender.

## Demo data (`data/demo/*.csv`)

Precomputed query results so the dashboard runs without AWS credentials. Same columns as the views above, plus `daily_spend.csv` (61 rows of `spend_date`, `daily_spend`) used for forecasting.

## Ownership (intended roles)

| Role | Responsible for | Here |
|---|---|---|
| **Data owner** (cloud cost or FinOps lead) | The thresholds and savings assumptions above, who may see spend data | Approves changes to `sql/finops_views.sql` definitions |
| **Data steward** (FinOps analyst) | Keeping this document accurate, reviewing failed quality checks | Maintains this file and runs the validation before analysis |
| **Data custodian** (data engineering) | S3, Glue, Athena, IAM, the pipeline itself | Runs ingestion and manages access |
