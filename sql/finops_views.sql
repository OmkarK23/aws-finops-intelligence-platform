CREATE OR REPLACE VIEW finops_database.vw_underutilized_resources AS
SELECT
    resource_id,
    service_name,
    region_zone,
    cpu_utilization_percent,
    memory_utilization_percent,
    rounded_cost_usd,
    usage_start_date,
    usage_end_date
FROM finops_database.gcp_cloud_billing
WHERE cpu_utilization_percent < 20;
SELECT *
FROM finops_database.vw_underutilized_resources
LIMIT 10;
CREATE OR REPLACE VIEW finops_database.vw_service_spend AS
SELECT
    service_name,
    ROUND(SUM(rounded_cost_usd), 2) AS total_cost,
    COUNT(DISTINCT resource_id) AS resource_count,
    ROUND(AVG(cpu_utilization_percent), 2) AS avg_cpu_utilization,
    ROUND(AVG(memory_utilization_percent), 2) AS avg_memory_utilization
FROM finops_database.gcp_cloud_billing
GROUP BY service_name
ORDER BY total_cost DESC;
SELECT *
FROM finops_database.vw_service_spend
LIMIT 10;
CREATE OR REPLACE VIEW finops_database.vw_region_spend AS
SELECT
    region_zone,
    ROUND(SUM(rounded_cost_usd), 2) AS total_cost,
    COUNT(DISTINCT resource_id) AS resource_count,
    ROUND(AVG(cpu_utilization_percent), 2) AS avg_cpu_utilization
FROM finops_database.gcp_cloud_billing
GROUP BY region_zone
ORDER BY total_cost DESC;
CREATE OR REPLACE VIEW finops_database.vw_optimization_recommendations AS
SELECT
    resource_id,
    service_name,
    region_zone,
    cpu_utilization_percent,
    memory_utilization_percent,
    rounded_cost_usd,
    CASE
        WHEN cpu_utilization_percent < 10 AND memory_utilization_percent < 25
            THEN 'High Risk - Terminate or Downsize'
        WHEN cpu_utilization_percent < 20
            THEN 'Medium Risk - Rightsize Resource'
        WHEN memory_utilization_percent < 30
            THEN 'Low Risk - Review Memory Allocation'
        ELSE 'Healthy'
    END AS recommendation,
    CASE
        WHEN cpu_utilization_percent < 10 AND memory_utilization_percent < 25
            THEN ROUND(rounded_cost_usd * 0.70, 2)
        WHEN cpu_utilization_percent < 20
            THEN ROUND(rounded_cost_usd * 0.40, 2)
        WHEN memory_utilization_percent < 30
            THEN ROUND(rounded_cost_usd * 0.20, 2)
        ELSE 0
    END AS estimated_savings_usd
FROM finops_database.gcp_cloud_billing;
SELECT *
FROM finops_database.vw_optimization_recommendations
WHERE estimated_savings_usd > 0
ORDER BY estimated_savings_usd DESC
LIMIT 20;
SELECT
    ROUND(SUM(rounded_cost_usd), 2) AS total_cloud_spend,
    COUNT(DISTINCT resource_id) AS total_resources,
    ROUND(SUM(CASE WHEN cpu_utilization_percent < 20 THEN rounded_cost_usd ELSE 0 END), 2) AS potential_waste,
    COUNT(CASE WHEN cpu_utilization_percent < 20 THEN 1 END) AS underutilized_resource_count
FROM finops_database.gcp_cloud_billing;
