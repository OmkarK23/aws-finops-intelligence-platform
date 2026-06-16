DEMO_MODE = True
import streamlit as st # type: ignore
import pandas as pd # type: ignore
import plotly.express as px # type: ignore
DEMO_MODE = True
if not DEMO_MODE:
    from pyathena import connect
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

st.set_page_config(
    page_title="Cloud FinOps Intelligence Platform",
    layout="wide"
)
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #f8fafc;
    }

    p, label, span {
        color: #cbd5e1;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #111827 100%);
    }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.25);
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 14px;
    }

    [data-testid="stMetricValue"] {
        color: #38bdf8;
        font-size: 28px;
        font-weight: 700;
    }

    div[data-testid="stTabs"] button {
        background-color: #1e293b;
        color: #e2e8f0;
        border-radius: 12px;
        padding: 10px 16px;
        margin-right: 6px;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        background-color: #2563eb;
        color: white;
    }

    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
    }

    .stAlert {
        border-radius: 14px;
    }
</style>
""", unsafe_allow_html=True)
ATHENA_S3_STAGING_DIR = "s3://finops-cost-lake-omkark23/athena-results/"
AWS_REGION = "us-east-1"


@st.cache_data(ttl=600)
def run_query(query):
    if DEMO_MODE:
        return pd.DataFrame()

    conn = connect(
        s3_staging_dir=ATHENA_S3_STAGING_DIR,
        region_name=AWS_REGION
    )

    return pd.read_sql(query, conn)


st.markdown("""
<div style="
    background: linear-gradient(90deg, #1d4ed8, #0f766e);
    padding: 28px;
    border-radius: 20px;
    margin-bottom: 24px;
">
    <h1 style="color:white; margin-bottom:8px;">
        Cloud FinOps Intelligence Platform
    </h1>
    <p style="color:#e0f2fe; font-size:18px;">
        Serverless AWS cost optimization, forecasting, and executive cloud spend intelligence.
    </p>
</div>
""", unsafe_allow_html=True)
st.info("""
Cloud FinOps Intelligence Platform analyzes cloud infrastructure costs, identifies optimization opportunities,
estimates savings, forecasts future spend, and provides executive-level FinOps insights using AWS serverless services.
""")
st.warning("""
Demo Mode: This public dashboard uses exported demo data for security. 
The production AWS backend supports automated refresh through S3 Event Notifications, AWS Lambda, AWS Glue, and Athena.
""")

st.caption("Demo dataset last refreshed: June 15, 2026")

kpi_query = """
SELECT
    ROUND(SUM(rounded_cost_usd), 2) AS total_cloud_spend,
    COUNT(DISTINCT resource_id) AS total_resources,
    ROUND(SUM(CASE WHEN cpu_utilization_percent < 20 THEN rounded_cost_usd ELSE 0 END), 2) AS potential_waste,
    COUNT(CASE WHEN cpu_utilization_percent < 20 THEN 1 END) AS underutilized_resource_count
FROM finops_database.gcp_cloud_billing;
"""

service_query = """
SELECT *
FROM finops_database.vw_service_spend
ORDER BY total_cost DESC;
"""

region_query = """
SELECT *
FROM finops_database.vw_region_spend
ORDER BY total_cost DESC;
"""

underutilized_query = """
SELECT *
FROM finops_database.vw_underutilized_resources
ORDER BY rounded_cost_usd DESC
LIMIT 50;
"""

recommendation_query = """
SELECT *
FROM finops_database.vw_optimization_recommendations
WHERE estimated_savings_usd > 0
ORDER BY estimated_savings_usd DESC
LIMIT 50;
"""

savings_query = """
SELECT
    ROUND(SUM(estimated_savings_usd), 2) AS estimated_savings
FROM finops_database.vw_optimization_recommendations
WHERE estimated_savings_usd > 0;
"""

top_savings_query = """
SELECT
    resource_id,
    service_name,
    estimated_savings_usd
FROM finops_database.vw_optimization_recommendations
WHERE estimated_savings_usd > 0
ORDER BY estimated_savings_usd DESC
LIMIT 1;
"""
forecast_query = """
SELECT
    CAST(date_parse(usage_start_date, '%d-%m-%Y %H:%i') AS date) AS spend_date,
    ROUND(SUM(rounded_cost_usd), 2) AS daily_spend
FROM finops_database.gcp_cloud_billing
GROUP BY 1
ORDER BY 1;
"""

if DEMO_MODE:

    service_df = pd.read_csv("data/demo/service_spend.csv")
    region_df = pd.read_csv("data/demo/region_spend.csv")
    underutilized_df = pd.read_csv("data/demo/underutilized.csv")
    recommendation_df = pd.read_csv("data/demo/recommendations.csv")
    forecast_df = pd.read_csv("data/demo/daily_spend.csv")

    kpi_df = pd.DataFrame([{
        "total_cloud_spend": service_df["total_cost"].sum(),
        "total_resources": service_df["resource_count"].sum(),
        "potential_waste": underutilized_df["rounded_cost_usd"].sum(),
        "underutilized_resource_count": len(underutilized_df)
    }])

    savings_df = pd.DataFrame([{
        "estimated_savings": recommendation_df["estimated_savings_usd"].sum()
    }])

    top_savings_df = recommendation_df.sort_values(
        "estimated_savings_usd",
        ascending=False
    ).head(1)

else:

    kpi_df = run_query(kpi_query)
    service_df = run_query(service_query)
    region_df = run_query(region_query)
    underutilized_df = run_query(underutilized_query)
    recommendation_df = run_query(recommendation_query)
    savings_df = run_query(savings_query)
    top_savings_df = run_query(top_savings_query)
    forecast_df = run_query(forecast_query)

kpi = kpi_df.iloc[0]
estimated_savings = savings_df.iloc[0]["estimated_savings"]
waste_pct = (kpi["potential_waste"] / kpi["total_cloud_spend"]) * 100

finops_score = max(
    0,
    round(100 - waste_pct)
)

with st.sidebar:
    st.title("Cloud FinOps")
    st.markdown("### Platform Overview")
    st.metric("Total Spend", f"${kpi['total_cloud_spend']:,.0f}")
    st.metric("Potential Waste", f"${kpi['potential_waste']:,.0f}")
    st.metric("Waste %", f"{waste_pct:.1f}%")
    st.metric("FinOps Health Score", f"{finops_score}/100")
    st.markdown("---")
    st.markdown("**Cloud Stack**")
    st.write("AWS S3")
    st.write("AWS Glue")
    st.write("Amazon Athena")
    st.write("Streamlit")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Executive Summary",
    "Service Analytics",
    "Resource Optimization",
    "Regional Analytics",
    "Forecasting",
    "Architecture"
])

with tab1:
    st.subheader("Executive Summary")
    st.markdown("### Platform Impact")

    impact1, impact2, impact3, impact4 = st.columns(4)

    impact1.metric("Resources Analyzed", "1,000")
    impact2.metric("Cloud Spend", "$2.1M+")
    impact3.metric("Potential Waste", "$420K+")
    impact4.metric("Savings Opportunities", "$278K+")
    st.success("""
        Data Pipeline Status

        ✓ S3 Data Lake  
        ✓ Lambda Automation  
        ✓ Glue Crawler  
        ✓ Glue ETL  
        ✓ Athena Analytics  
        ✓ Forecast Engine
        """)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Total Cloud Spend", f"${kpi['total_cloud_spend']:,.0f}")
    col2.metric("Total Resources", f"{int(kpi['total_resources']):,}")
    col3.metric("Potential Waste", f"${kpi['potential_waste']:,.0f}")
    col4.metric("Waste %", f"{waste_pct:.1f}%")
    col5.metric("Estimated Savings", f"${estimated_savings:,.0f}")
    col6.metric("FinOps Score", f"{finops_score}/100")

    st.info(
        f"Top Savings Opportunity: "
        f"{top_savings_df.iloc[0]['resource_id']} | "
        f"{top_savings_df.iloc[0]['service_name']} | "
        f"${top_savings_df.iloc[0]['estimated_savings_usd']:,.0f}"
    )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        fig_service = px.bar(
            service_df.head(10),
            x="service_name",
            y="total_cost",
            title="Top 10 Services by Spend"
        )
        st.plotly_chart(fig_service, use_container_width=True)

    with col_b:
        fig_region = px.bar(
            region_df.head(10),
            x="region_zone",
            y="total_cost",
            title="Top 10 Regions by Spend"
        )
        st.plotly_chart(fig_region, use_container_width=True)

with tab2:
    st.subheader("Service Analytics")

    fig_service_full = px.bar(
        service_df,
        x="service_name",
        y="total_cost",
        title="Cloud Spend by Service"
    )
    st.plotly_chart(fig_service_full, use_container_width=True)

    fig_service_pie = px.pie(
        service_df,
        names="service_name",
        values="total_cost",
        title="Service Spend Distribution"
    )
    st.plotly_chart(fig_service_pie, use_container_width=True)

    st.dataframe(service_df, use_container_width=True)

with tab3:
    st.subheader("Resource Optimization")

    col1, col2, col3 = st.columns(3)

    col1.metric("Underutilized Resources", f"{int(kpi['underutilized_resource_count']):,}")
    col2.metric("Potential Waste", f"${kpi['potential_waste']:,.0f}")
    col3.metric("Estimated Savings", f"${estimated_savings:,.0f}")

    st.divider()

    recommendation_display = recommendation_df.rename(
        columns={
            "resource_id": "Resource ID",
            "service_name": "Service",
            "region_zone": "Region",
            "cpu_utilization_percent": "CPU %",
            "memory_utilization_percent": "Memory %",
            "rounded_cost_usd": "Monthly Cost ($)",
            "estimated_savings_usd": "Savings Opportunity ($)",
            "recommendation": "Recommendation"
        }
    )

    underutilized_display = underutilized_df.rename(
        columns={
            "resource_id": "Resource ID",
            "service_name": "Service",
            "region_zone": "Region",
            "cpu_utilization_percent": "CPU %",
            "memory_utilization_percent": "Memory %",
            "rounded_cost_usd": "Monthly Cost ($)",
            "usage_start_date": "Usage Start Date",
            "usage_end_date": "Usage End Date"
        }
    )

    st.markdown("### Top Optimization Recommendations")
    st.dataframe(recommendation_display, use_container_width=True)

    fig_savings = px.bar(
        recommendation_display.head(20),
        x="Resource ID",
        y="Savings Opportunity ($)",
        color="Recommendation",
        title="Top 20 Estimated Savings Opportunities"
    )
    st.plotly_chart(fig_savings, use_container_width=True)

    st.markdown("### Underutilized Resources")
    st.dataframe(underutilized_display, use_container_width=True)

with tab4:
    st.subheader("Regional Analytics")

    fig_region_full = px.bar(
        region_df,
        x="region_zone",
        y="total_cost",
        title="Cloud Spend by Region"
    )
    st.plotly_chart(fig_region_full, use_container_width=True)

    st.dataframe(region_df, use_container_width=True)

with tab5:
    st.subheader("Spend Forecasting & Budget Risk")

    if not PROPHET_AVAILABLE:
        st.warning("Prophet is not installed. Forecasting is unavailable in this environment.")
    else:
        forecast_data = forecast_df.rename(
            columns={
                "spend_date": "ds",
                "daily_spend": "y"
            }
        )

        forecast_data["ds"] = pd.to_datetime(forecast_data["ds"])
        forecast_data["y"] = pd.to_numeric(forecast_data["y"])

        if len(forecast_data) >= 10:
            model = Prophet()
            model.fit(forecast_data)

            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)

            historical_spend = forecast_data["y"].sum()
            projected_next_30_days = forecast.tail(30)["yhat"].sum()
            budget_limit = historical_spend * 1.05

            if projected_next_30_days > budget_limit:
                risk_status = "High Budget Risk"
            elif projected_next_30_days > historical_spend:
                risk_status = "Medium Budget Risk"
            else:
                risk_status = "Low Budget Risk"

            col1, col2, col3 = st.columns(3)

            col1.metric("Historical Spend", f"${historical_spend:,.0f}")
            col2.metric("Projected Next 30 Days", f"${projected_next_30_days:,.0f}")
            with col3:
                st.markdown("### Budget Risk")

                if risk_status == "High Budget Risk":
                    st.error("🔴 Budget Exceedance Likely")

                elif risk_status == "Medium Budget Risk":
                    st.warning("🟡 Monitor Spending Trend")

                else:
                    st.success("🟢 Within Budget Forecast")

            fig_forecast = px.line(
                forecast,
                x="ds",
                y="yhat",
                title="Cloud Spend Forecast - Next 30 Days"
            )

            st.plotly_chart(fig_forecast, use_container_width=True)

            forecast_display = forecast[
                ["ds", "yhat", "yhat_lower", "yhat_upper"]
            ].tail(30).copy()

            forecast_display["ds"] = forecast_display["ds"].dt.strftime("%b %d, %Y")

            st.dataframe(
                forecast_display,
                use_container_width=True
        )
        else:
            st.warning("Not enough historical dates for reliable forecasting.")
with tab6:
    st.subheader("Cloud FinOps Architecture")

    st.image(
        "docs/architecture/aws_finops_architecture.png",
        use_container_width=True
    )

    st.markdown("""
    **Architecture Components**

    - Amazon S3 Data Lake
    - AWS Lambda Automation
    - AWS Glue Crawlers
    - AWS Glue ETL
    - AWS Glue Catalog
    - Amazon Athena
    - Streamlit Dashboard
    - Forecasting & FinOps Analytics
    """)
st.divider()

st.caption(
    "Built with AWS S3, Lambda, Glue, Athena, Streamlit, Plotly, and Prophet."
)