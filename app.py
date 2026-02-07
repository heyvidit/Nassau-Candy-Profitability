import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# -----------------------------
# PAGE CONFIGURATION
# -----------------------------
st.set_page_config(
    page_title="Nassau Candy | Profitability Dashboard",
    layout="wide"
)

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")
    # Basic cleaning
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    return df

df = load_data()

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

# -----------------------------
# PAGE NAVIGATION
# -----------------------------
page = st.sidebar.radio(
    "Select Dashboard Page",
    ["Overview", "Product Profitability", "Division Performance", "Cost & Margin Diagnostics", "Pareto Analysis"]
)

# -----------------------------
# APPLY FILTERS
# -----------------------------
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
product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]

# -----------------------------
# OVERVIEW PAGE
# -----------------------------
if page == "Overview":
    st.title("🍫 Nassau Candy Distributor | Overview")
    st.subheader("High-Level KPIs & Division Snapshot")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${filtered_df['Sales'].sum():,.0f}")
    col2.metric("Total Profit", f"${filtered_df['Gross Profit'].sum():,.0f}")
    col3.metric("Average Gross Margin", f"{filtered_df['Gross Margin %'].mean()*100:.2f}%")
    col4.metric("Total Units Sold", f"{filtered_df['Units'].sum():,.0f}")

    # Division Revenue vs Profit
    division_perf = (
        filtered_df.groupby("Division", as_index=False)
        .agg(Revenue=("Sales", "sum"), Profit=("Gross Profit", "sum"), Avg_Margin=("Gross Margin %", "mean"))
    )

    st.subheader("Revenue vs Profit by Division")
    fig, ax = plt.subplots(figsize=(8,4))
    sns.barplot(
        data=division_perf.melt(id_vars="Division", value_vars=["Revenue","Profit"]),
        x="Division", y="value", hue="variable", ax=ax
    )
    ax.set_ylabel("USD")
    ax.set_title("Revenue vs Profit by Division")
    st.pyplot(fig)

# -----------------------------
# PRODUCT PROFITABILITY PAGE
# -----------------------------
elif page == "Product Profitability":
    st.title("📦 Product Profitability")
    st.subheader("Leaderboard & Insights")

    # Sortable table with color coding
    product_table = product_perf.sort_values("Total_Profit", ascending=False)
    st.dataframe(
        product_table.style.background_gradient(subset=["Avg_Gross_Margin"], cmap="RdYlGn")
    )

    # Top 10 Products by Profit
    st.subheader("Top 10 Products by Profit")
    top10 = product_table.head(10)
    fig, ax = plt.subplots(figsize=(10,5))
    sns.barplot(
        data=top10,
        x="Total_Profit", y="Product Name", hue="Division", dodge=False, palette="Set2", ax=ax
    )
    ax.set_xlabel("Total Profit (USD)")
    ax.set_ylabel("")
    ax.set_title("Top 10 Products by Profit")
    st.pyplot(fig)

# -----------------------------
# DIVISION PERFORMANCE PAGE
# -----------------------------
elif page == "Division Performance":
    st.title("🏭 Division Performance")
    st.subheader("Revenue, Profit & Margin Distribution")

    fig, ax = plt.subplots(figsize=(8,4))
    sns.barplot(
        data=division_perf.melt(id_vars="Division", value_vars=["Revenue","Profit"]),
        x="Division", y="value", hue="variable", ax=ax
    )
    ax.set_ylabel("USD")
    ax.set_title("Revenue vs Profit by Division")
    st.pyplot(fig)

    st.subheader("Average Gross Margin by Division")
    fig2, ax2 = plt.subplots(figsize=(8,4))
    sns.barplot(
        data=division_perf, x="Division", y="Avg_Margin", palette="RdYlGn", ax=ax2
    )
    ax2.set_ylabel("Average Gross Margin")
    st.pyplot(fig2)

# -----------------------------
# COST & MARGIN DIAGNOSTICS PAGE
# -----------------------------
elif page == "Cost & Margin Diagnostics":
    st.title("⚠️ Cost vs Margin Diagnostics")

    fig, ax = plt.subplots(figsize=(8,5))
    sns.scatterplot(
        data=filtered_df, x="Cost", y="Gross Margin %", hue="Division", palette="Set1", s=80, ax=ax
    )
    ax.axhline(y=0.2, color='red', linestyle='--', label='20% Margin Threshold')
    ax.set_ylabel("Gross Margin")
    ax.set_title("Cost vs Gross Margin by Product")
    ax.legend()
    st.pyplot(fig)

# -----------------------------
# PARETO ANALYSIS PAGE
# -----------------------------
elif page == "Pareto Analysis":
    st.title("📊 Profit Concentration / Pareto Analysis")

    pareto = product_perf.sort_values("Total_Profit", ascending=False)
    pareto["Cumulative Profit %"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum()

    fig, ax = plt.subplots(figsize=(10,5))
    sns.lineplot(data=pareto, y="Cumulative Profit %", x=range(len(pareto)), marker="o", ax=ax)
    ax.axhline(0.8, linestyle="--", color="red", label="80% Threshold")
    ax.set_xlabel("Products (Ranked by Profit)")
    ax.set_ylabel("Cumulative Profit %")
    ax.set_title("Cumulative Profit Contribution (Pareto)")
    ax.legend()
    st.pyplot(fig)

    st.subheader("Top Products contributing to 80% of Profit")
    top_products = pareto[pareto["Cumulative Profit %"] <= 0.8]
    st.dataframe(top_products[["Product Name","Division","Total_Profit","Cumulative Profit %"]])

# -----------------------------
# OPTIONAL: DOWNLOAD FILTERED DATA
# -----------------------------
st.sidebar.download_button(
    "Download Filtered Data (CSV)",
    filtered_df.to_csv(index=False),
    "Filtered_NassauCandy.csv"
)

st.caption("Built for strategic profitability decision-making at Nassau Candy Distributor")
