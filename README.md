![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20Glue%20%7C%20Athena-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![FinOps](https://img.shields.io/badge/FinOps-Cost%20Optimization-green)

# Cloud FinOps Intelligence Platform

A serverless cloud cost analytics and optimization platform built using AWS S3, AWS Glue, Amazon Athena, Python, and Streamlit.

## Business Problem

Cloud teams often struggle to identify where infrastructure costs are increasing, which services drive spend, and which resources are underutilized. This project solves that problem by analyzing cloud billing and utilization data to identify waste, forecast future spend, and generate FinOps optimization recommendations.

## Key Results

- Analyzed 1,000 cloud resource billing records
- Processed $2.13M+ in cloud spend
- Identified $420K+ in potential waste
- Estimated $278K+ in savings opportunities
- Detected 193 underutilized resources
- Built forecasting and budget risk analysis using 61 days of spend data

## Architecture

```text
GCP Billing Dataset
        ↓
Amazon S3 Data Lake
        ↓
AWS Glue Data Catalog
        ↓
Amazon Athena SQL Engine
        ↓
Athena Views / FinOps Optimization Layer
        ↓
Streamlit Dashboard
        ↓
Executive KPIs + Forecasting + Budget Risk

## Repository Structure

```text
.
├── dashboard/
│   └── app.py
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── architecture/
│   └── screenshots/
├── notebooks/
├── sql/
│   └── finops_views.sql
├── src/
├── requirements.txt
└── README.md
```
## Architecture

![Architecture](docs/architecture/aws_finops_architecture.png)

## Dashboard Screenshots

### Executive Summary
![Executive Summary](docs/screenshots/executive_summary.png)

### Resource Optimization
![Resource Optimization](docs/screenshots/resource_optimization.png)

### Forecasting
![Forecasting](docs/screenshots/forecasting.png)