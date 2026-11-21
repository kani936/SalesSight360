
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="SalesSight 360",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

# =====================================================
# 2. PROFESSIONAL WEBSITE STYLING
# =====================================================

st.markdown("""
<style>
    .stApp {
        background-color: #F4F7FB;
        color: #243447;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4 {
        color: #142D4E !important;
        font-weight: 700 !important;
    }

    p, label, .stMarkdown, .stCaption {
        color: #243447 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #142D4E;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(20,45,78,0.05);
    }

    [data-testid="stMetricLabel"] {
        color: #64748B !important;
    }

    [data-testid="stMetricValue"] {
        color: #142D4E !important;
        font-weight: 700;
    }

    div[data-testid="stPlotlyChart"] {
        background-color: white;
        border-radius: 12px;
        padding: 10px;
    }

    hr {
        border-color: #DCE4EF;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 3. LOAD CLEANED DATASETS
# =====================================================

@st.cache_data
def load_data(filename):
    file_path = DATA_DIR / filename

    if file_path.exists():
        return pd.read_csv(file_path)

    return pd.DataFrame()


leads = load_data("crm_leads_cleaned.csv")
orders = load_data("orders_cleaned.csv")
reps = load_data("sales_reps_cleaned.csv")
products = load_data("products_cleaned.csv")
payments = load_data("payments_cleaned.csv")
targets = load_data("sales_targets_cleaned.csv")
history = load_data("lead_stage_history_cleaned.csv")

# =====================================================
# 4. CHECK REQUIRED DATA
# =====================================================

st.markdown("""
<h1 style="color:#142D4E;">📊 SalesSight 360</h1>
<p style="color:#64748B !important; font-size:17px;">
Multi-Channel Revenue Analytics Platform
</p>
""", unsafe_allow_html=True)

st.markdown("---")

if leads.empty or orders.empty:
    st.error(
        "Required datasets were not found. "
        "Please check the data/processed folder and CSV filenames."
    )

    st.write("Expected files:")
    st.code("""
crm_leads_cleaned.csv
orders_cleaned.csv
sales_reps_cleaned.csv
products_cleaned.csv
payments_cleaned.csv
sales_targets_cleaned.csv
lead_stage_history_cleaned.csv
    """)

    st.stop()

# =====================================================
# 5. PREPARE DATA
# =====================================================

leads["lead_date"] = pd.to_datetime(
    leads["lead_date"], errors="coerce"
)

orders["order_date"] = pd.to_datetime(
    orders["order_date"], errors="coerce"
)

if "month" in targets.columns:
    targets["month"] = pd.to_datetime(
        targets["month"], errors="coerce"
    )

# Convert numerical columns safely

leads["expected_deal_value"] = pd.to_numeric(
    leads["expected_deal_value"], errors="coerce"
).fillna(0)

orders["revenue"] = pd.to_numeric(
    orders["revenue"], errors="coerce"
).fillna(0)

# Add representative details to leads

if not reps.empty:
    rep_columns = [
        col for col in ["rep_id", "rep_name", "team", "region"]
        if col in reps.columns
    ]

    if "rep_id" in rep_columns:
        leads = leads.merge(
            reps[rep_columns].drop_duplicates("rep_id"),
            on="rep_id",
            how="left",
            suffixes=("", "_rep")
        )

# Delivered orders only

if "order_status" in orders.columns:
    delivered = orders[
        orders["order_status"].astype(str).str.lower()
        == "delivered"
    ].copy()
else:
    delivered = orders.copy()

# =====================================================
# 6. SIDEBAR NAVIGATION
# =====================================================

st.sidebar.markdown("""
# 📊 SalesSight 360
### SALES INTELLIGENCE
""")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Executive Overview",
        "Sales Funnel Analysis",
        "Pipeline & Forecast",
        "Performance Analysis"
    ]
)

# =====================================================
# 7. SIDEBAR FILTERS
# =====================================================

st.sidebar.markdown("---")
st.sidebar.subheader("REPORT FILTERS")

regions = (
    sorted(leads["region"].dropna().unique().tolist())
    if "region" in leads.columns else []
)

channels = (
    sorted(leads["channel"].dropna().unique().tolist())
    if "channel" in leads.columns else []
)

selected_regions = st.sidebar.multiselect(
    "Select Region",
    regions,
    default=regions
)

selected_channels = st.sidebar.multiselect(
    "Select Channel",
    channels,
    default=channels
)

# Apply lead filters

filtered_leads = leads.copy()

if "region" in filtered_leads.columns:
    filtered_leads = filtered_leads[
        filtered_leads["region"].isin(selected_regions)
    ]

if "channel" in filtered_leads.columns:
    filtered_leads = filtered_leads[
        filtered_leads["channel"].isin(selected_channels)
    ]

# Filter orders using selected lead IDs

selected_lead_ids = filtered_leads["lead_id"].unique()

filtered_orders = orders[
    orders["lead_id"].isin(selected_lead_ids)
].copy()

filtered_delivered = filtered_orders.copy()

if "order_status" in filtered_delivered.columns:
    filtered_delivered = filtered_delivered[
        filtered_delivered["order_status"].astype(str).str.lower()
        == "delivered"
    ]

# =====================================================
# 8. CALCULATE FILTERED KPIs
# =====================================================

total_leads = len(filtered_leads)

won_deals = (
    filtered_leads["stage"] == "Closed Won"
).sum()

lost_deals = (
    filtered_leads["stage"] == "Closed Lost"
).sum()

win_rate = (
    won_deals / (won_deals + lost_deals)
    if won_deals + lost_deals > 0 else 0
)

delivered_revenue = filtered_delivered["revenue"].sum()

average_deal_size = (
    filtered_delivered["revenue"].mean()
    if not filtered_delivered.empty else 0
)

open_leads = filtered_leads[
    ~filtered_leads["stage"].isin(
        ["Closed Won", "Closed Lost"]
    )
]

total_pipeline = open_leads["expected_deal_value"].sum()

stage_probabilities = {
    "New": 0.05,
    "Contacted": 0.10,
    "Qualified": 0.25,
    "Proposal": 0.50,
    "Negotiation": 0.75,
    "Closed Won": 1.00,
    "Closed Lost": 0.00
}

open_leads = open_leads.copy()

open_leads["Probability"] = (
    open_leads["stage"].map(stage_probabilities).fillna(0)
)

open_leads["Weighted Value"] = (
    open_leads["expected_deal_value"]
    * open_leads["Probability"]
)

weighted_pipeline = open_leads["Weighted Value"].sum()

# Successful payments for selected leads

successful_payments = 0

if not payments.empty:
    selected_order_ids = filtered_orders["order_id"].unique()

    selected_payments = payments[
        payments["order_id"].isin(selected_order_ids)
    ].copy()

    if {"payment_status", "amount"}.issubset(selected_payments.columns):
        successful_payments = pd.to_numeric(
            selected_payments.loc[
                selected_payments["payment_status"].astype(str).str.lower()
                == "success",
                "amount"
            ],
            errors="coerce"
        ).fillna(0).sum()

# =====================================================
# 9. EXECUTIVE OVERVIEW
# =====================================================

if page == "Executive Overview":

    st.header("Executive Overview")

    st.write(
        "Monitor overall sales performance, revenue trends "
        "and business growth."
    )

    # KPI ROW 1

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Leads", f"{total_leads:,}")
    c2.metric("Won Deals", f"{won_deals:,}")
    c3.metric("Win Rate", f"{win_rate:.2%}")
    c4.metric("Delivered Revenue", f"₹{delivered_revenue:,.0f}")

    # KPI ROW 2

    c5, c6, c7, c8 = st.columns(4)

    c5.metric(
        "Average Deal Size",
        f"₹{average_deal_size:,.0f}"
    )

    c6.metric(
        "Total Pipeline",
        f"₹{total_pipeline:,.0f}"
    )

    c7.metric(
        "Weighted Pipeline",
        f"₹{weighted_pipeline:,.0f}"
    )

    c8.metric(
        "Successful Payments",
        f"₹{successful_payments:,.0f}"
    )

    st.markdown("---")

    left, right = st.columns(2)

    # Monthly revenue

    with left:

        st.subheader("Monthly Delivered Revenue")

        if not filtered_delivered.empty:

            monthly = filtered_delivered.copy()

            monthly["Month"] = (
                monthly["order_date"]
                .dt.to_period("M").astype(str)
            )

            trend = monthly.groupby(
                "Month", as_index=False
            )["revenue"].sum()

            fig = px.line(
                trend,
                x="Month",
                y="revenue",
                markers=True,
                title="Revenue Trend"
            )

            fig.update_traces(
                line_color="#20A39E",
                line_width=3
            )

            st.plotly_chart(
                fig, use_container_width=True
            )

        else:
            st.info("No delivered revenue for the selected filters.")

    # Lead stage distribution

    with right:

        st.subheader("Current Lead Stage Distribution")

        stage_data = (
            filtered_leads["stage"]
            .value_counts()
            .reset_index()
        )

        stage_data.columns = ["Stage", "Count"]

        fig = px.pie(
            stage_data,
            names="Stage",
            values="Count",
            hole=0.45
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

    # Regional revenue

    if "region" in filtered_leads.columns:

        st.subheader("Regional Revenue")

        region_data = filtered_leads[
            ["lead_id", "region"]
        ].merge(
            filtered_delivered[["lead_id", "revenue"]],
            on="lead_id",
            how="inner"
        )

        region_summary = region_data.groupby(
            "region", as_index=False
        )["revenue"].sum()

        fig = px.bar(
            region_summary,
            x="region",
            y="revenue",
            color="region",
            title="Delivered Revenue by Region"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

# =====================================================
# 10. SALES FUNNEL ANALYSIS
# =====================================================

elif page == "Sales Funnel Analysis":

    st.header("Sales Funnel Analysis")

    st.write(
        "Understand lead distribution, stage performance "
        "and channel effectiveness."
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Leads", f"{total_leads:,}")
    c2.metric("Won Deals", f"{won_deals:,}")
    c3.metric("Win Rate", f"{win_rate:.2%}")

    st.markdown("---")

    left, right = st.columns(2)

    # Current stage distribution

    with left:

        st.subheader("Current Stage Distribution")

        stage_data = (
            filtered_leads["stage"]
            .value_counts()
            .reset_index()
        )

        stage_data.columns = ["Stage", "Count"]

        fig = px.funnel(
            stage_data,
            x="Count",
            y="Stage",
            title="Lead Distribution by Current Stage"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

    # Channel distribution

    with right:

        st.subheader("Lead Source Distribution")

        channel_data = (
            filtered_leads["channel"]
            .value_counts()
            .reset_index()
        )

        channel_data.columns = ["Channel", "Leads"]

        fig = px.bar(
            channel_data,
            x="Channel",
            y="Leads",
            color="Channel",
            title="Leads by Channel"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

    # Monthly leads

    st.subheader("Monthly Lead Trend")

    monthly = filtered_leads.copy()

    monthly["Month"] = (
        monthly["lead_date"].dt.to_period("M").astype(str)
    )

    trend = monthly.groupby(
        "Month", as_index=False
    ).size()

    trend.columns = ["Month", "Leads"]

    fig = px.line(
        trend,
        x="Month",
        y="Leads",
        markers=True
    )

    st.plotly_chart(
        fig, use_container_width=True
    )

    # Channel-wise win rate

    st.subheader("Channel-wise Win Rate")

    channel_results = []

    for channel, group in filtered_leads.groupby("channel"):

        channel_won = (
            group["stage"] == "Closed Won"
        ).sum()

        channel_lost = (
            group["stage"] == "Closed Lost"
        ).sum()

        denominator = channel_won + channel_lost

        rate = (
            channel_won / denominator
            if denominator > 0 else 0
        )

        channel_results.append({
            "Channel": channel,
            "Win Rate": rate * 100
        })

    channel_results = pd.DataFrame(channel_results)

    fig = px.bar(
        channel_results,
        x="Channel",
        y="Win Rate",
        color="Channel",
        title="Win Rate by Channel",
        labels={"Win Rate": "Win Rate (%)"}
    )

    st.plotly_chart(
        fig, use_container_width=True
    )

# =====================================================
# 11. PIPELINE & FORECAST
# =====================================================

elif page == "Pipeline & Forecast":

    st.header("Pipeline & Forecast")

    st.write(
        "Analyse open opportunities, weighted pipeline "
        "and monthly sales target performance."
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Pipeline",
        f"₹{total_pipeline:,.0f}"
    )

    c2.metric(
        "Weighted Pipeline",
        f"₹{weighted_pipeline:,.0f}"
    )

    c3.metric(
        "Delivered Revenue",
        f"₹{delivered_revenue:,.0f}"
    )

    st.markdown("---")

    left, right = st.columns(2)

    # Open pipeline by stage

    with left:

        st.subheader("Open Pipeline by Stage")

        stage_pipeline = open_leads.groupby(
            "stage", as_index=False
        )["expected_deal_value"].sum()

        fig = px.bar(
            stage_pipeline,
            x="stage",
            y="expected_deal_value",
            color="stage",
            title="Pipeline Value by Stage"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

    # Weighted pipeline by stage

    with right:

        st.subheader("Weighted Pipeline by Stage")

        weighted_stage = open_leads.groupby(
            "stage", as_index=False
        )["Weighted Value"].sum()

        fig = px.bar(
            weighted_stage,
            x="stage",
            y="Weighted Value",
            color="stage",
            title="Weighted Pipeline Value"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

    # Monthly targets

    st.markdown("---")
    st.subheader("Monthly Revenue vs Sales Target")

    if not targets.empty and "month" in targets.columns:

        target_data = targets.copy()

        target_data["Month"] = (
            target_data["month"]
            .dt.to_period("M").astype(str)
        )

        target_summary = target_data.groupby(
            "Month", as_index=False
        )["sales_target"].sum()

        actual_data = filtered_delivered.copy()

        actual_data["Month"] = (
            actual_data["order_date"]
            .dt.to_period("M").astype(str)
        )

        actual_summary = actual_data.groupby(
            "Month", as_index=False
        )["revenue"].sum()

        comparison = target_summary.merge(
            actual_summary,
            on="Month",
            how="left"
        ).fillna(0)

        comparison["Variance"] = (
            comparison["revenue"]
            - comparison["sales_target"]
        )

        comparison["Achievement %"] = (
            comparison["revenue"]
            / comparison["sales_target"].replace(0, pd.NA)
            * 100
        )

        fig = px.bar(
            comparison,
            x="Month",
            y=["sales_target", "revenue"],
            barmode="group",
            title="Monthly Target vs Actual Revenue",
            labels={
                "value": "Amount",
                "variable": "Metric"
            }
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

        st.subheader("Monthly Target Details")

        st.dataframe(
            comparison,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Sales target data is unavailable.")

# =====================================================
# 12. PERFORMANCE ANALYSIS
# =====================================================

elif page == "Performance Analysis":

    st.header("Performance Analysis")

    st.write(
        "Explore sales performance across regions, teams "
        "and individual representatives."
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Filtered Leads", f"{total_leads:,}")
    c2.metric("Won Deals", f"{won_deals:,}")
    c3.metric(
        "Delivered Revenue",
        f"₹{delivered_revenue:,.0f}"
    )

    st.markdown("---")

    # Revenue by region

    if "region" in filtered_leads.columns:

        st.subheader("Revenue by Region")

        region_data = filtered_leads[
            ["lead_id", "region"]
        ].merge(
            filtered_delivered[["lead_id", "revenue"]],
            on="lead_id",
            how="inner"
        )

        region_summary = region_data.groupby(
            "region", as_index=False
        )["revenue"].sum()

        fig = px.bar(
            region_summary,
            x="region",
            y="revenue",
            color="region",
            title="Regional Sales Performance"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

    # Revenue by team

    if "team" in filtered_leads.columns:

        st.subheader("Revenue by Team")

        team_data = filtered_leads[
            ["lead_id", "team"]
        ].merge(
            filtered_delivered[["lead_id", "revenue"]],
            on="lead_id",
            how="inner"
        )

        team_summary = team_data.groupby(
            "team", as_index=False
        )["revenue"].sum()

        fig = px.bar(
            team_summary,
            x="team",
            y="revenue",
            color="team",
            title="Team-wise Revenue"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

    # Revenue by representative

    if "rep_name" in filtered_leads.columns:

        st.subheader("Revenue by Sales Representative")

        rep_data = filtered_leads[
            ["lead_id", "rep_name"]
        ].merge(
            filtered_delivered[["lead_id", "revenue"]],
            on="lead_id",
            how="inner"
        )

        rep_summary = rep_data.groupby(
            "rep_name", as_index=False
        )["revenue"].sum()

        rep_summary = rep_summary.sort_values(
            "revenue", ascending=False
        )

        fig = px.bar(
            rep_summary,
            x="rep_name",
            y="revenue",
            color="revenue",
            title="Representative-wise Revenue"
        )

        st.plotly_chart(
            fig, use_container_width=True
        )

        st.subheader("Representative Performance Details")

        st.dataframe(
            rep_summary,
            use_container_width=True,
            hide_index=True
        )

# =====================================================
# 13. FOOTER
# =====================================================

st.markdown("---")

st.markdown("""
<div style="text-align:center; padding:15px;">
    <h4 style="color:#142D4E;">SalesSight 360</h4>
    <p style="color:#64748B !important;">
        Multi-Channel Revenue Analytics Platform
        <br>
        Analytics prototype using synthetic project data
    </p>
</div>
""", unsafe_allow_html=True)
