
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Nassau Candy | Profitability Analysis", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    return df

df = load_data()

st.title("🍫 Nassau Candy Distributor")
st.subheader("Product Line Profitability & Margin Performance Dashboard")

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Filters")

division_filter = st.sidebar.multiselect(
    "Select Division",
    options=df["Division"].unique(),
    default=df["Division"].unique()
)

date_range = st.sidebar.date_input(
    "Order Date Range",
    [df["Order Date"].min(), df["Order Date"].max()]
)

margin_threshold = st.sidebar.slider(
    "Minimum Gross Margin (%)",
    min_value=0,
    max_value=100,
    value=0
)

product_search = st.sidebar.text_input("Search Product")

# Apply filters
filtered_df = df[
    (df["Division"].isin(division_filter)) &
    (df["Order Date"] >= pd.to_datetime(date_range[0])) &
    (df["Order Date"] <= pd.to_datetime(date_range[1])) &
    (df["Gross Margin %"] * 100 >= margin_threshold)
]

if product_search:
    filtered_df = filtered_df[
        filtered_df["Product Name"].str.contains(product_search, case=False)
    ]

# -----------------------------
# PRODUCT-LEVEL AGGREGATION
# -----------------------------
product_perf = (
    filtered_df.groupby(["Division", "Product Name"], as_index=False)
    .agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Avg_Gross_Margin=("Gross Margin %", "mean")
    )
)

product_perf["Profit per Unit"] = (
    product_perf["Total_Profit"] / product_perf["Total_Units"]
)

# -----------------------------
# KPI METRICS
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Revenue", f"${filtered_df['Sales'].sum():,.0f}")
col2.metric("Total Profit", f"${filtered_df['Gross Profit'].sum():,.0f}")
col3.metric("Avg Gross Margin", f"{filtered_df['Gross Margin %'].mean()*100:.2f}%")

# -----------------------------
# PRODUCT PROFITABILITY LEADERBOARD
# -----------------------------
st.header("📦 Product Profitability Leaderboard")

st.dataframe(
    product_perf.sort_values("Total_Profit", ascending=False),
    use_container_width=True
)

# -----------------------------
# DIVISION PERFORMANCE
# -----------------------------
st.header("🏭 Division Performance")

division_perf = (
    filtered_df.groupby("Division", as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Gross Profit", "sum"),
        Avg_Margin=("Gross Margin %", "mean")
    )
)

fig, ax = plt.subplots()
ax.bar(division_perf["Division"], division_perf["Revenue"], label="Revenue")
ax.bar(division_perf["Division"], division_perf["Profit"], label="Profit")
ax.set_title("Revenue vs Profit by Division")
ax.legend()

st.pyplot(fig)

# -----------------------------
# COST VS MARGIN DIAGNOSTICS
# -----------------------------
st.header("⚠️ Cost vs Margin Diagnostics")

fig2, ax2 = plt.subplots()
ax2.scatter(filtered_df["Cost"], filtered_df["Gross Margin %"])
ax2.set_xlabel("Cost")
ax2.set_ylabel("Gross Margin")
ax2.set_title("Cost vs Gross Margin")

st.pyplot(fig2)

# -----------------------------
# PARETO ANALYSIS
# -----------------------------
st.header("📊 Profit Concentration (Pareto Analysis)")

pareto = product_perf.sort_values("Total_Profit", ascending=False)
pareto["Cumulative Profit %"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum()

fig3, ax3 = plt.subplots()
ax3.plot(pareto["Cumulative Profit %"].values)
ax3.axhline(0.8, linestyle="--")
ax3.set_title("Cumulative Profit Contribution")

st.pyplot(fig3)

st.caption("Built for strategic profitability decision-making at Nassau Candy Distributor")
