import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Set global styles for seaborn & matplotlib
sns.set_style("whitegrid")
sns.set_palette("Set2")

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

page = st.sidebar.radio(
    "Select Dashboard Page",
    options=[
        "Overview",
        "Product Profitability",
        "Division Performance",
        "Cost & Margin Diagnostics",
        "Pareto Analysis"
    ]
)

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
product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]

# -----------------------------
# KPI METRICS - only on Overview page
# -----------------------------
def show_kpis():
    total_revenue = filtered_df['Sales'].sum()
    total_profit = filtered_df['Gross Profit'].sum()
    avg_margin = filtered_df['Gross Margin %'].mean() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Avg Gross Margin", f"{avg_margin:.2f}%")

# -----------------------------
# FORMATTING HELPERS
# -----------------------------
def currency_fmt(x, pos):
    return f'${x:,.0f}'

def percent_fmt(x, pos):
    return f'{x*100:.0f}%'

# -----------------------------
# PAGE: Overview
# -----------------------------
def page_overview():
    st.title("🍫 Nassau Candy Distributor")
    st.subheader("Executive Overview")

    show_kpis()

    st.markdown(
        """
        This dashboard provides comprehensive insights into product line profitability, division performance, and margin diagnostics for Nassau Candy Distributor.
        Use the sidebar to filter data and navigate pages.
        """
    )

# -----------------------------
# PAGE: Product Profitability
# -----------------------------
def page_product_profitability():
    st.title("📦 Product Profitability Leaderboard")
    
    # Sort and show top 20 by total profit for clarity
    top_products = product_perf.sort_values("Total_Profit", ascending=False).head(20)

    # Highlight columns with conditional formatting
    styled_df = top_products.style.format({
        'Total_Sales': "${:,.0f}",
        'Total_Profit': "${:,.0f}",
        'Profit per Unit': "${:,.2f}",
        'Avg_Gross_Margin': "{:.2%}"
    }).background_gradient(subset=['Avg_Gross_Margin', 'Total_Profit'], cmap="RdYlGn")

    st.dataframe(styled_df, use_container_width=True)

    # Bar plot: Top Products by Total Profit (Horizontal)
    fig, ax = plt.subplots(figsize=(10,6))
    sns.barplot(
        data=top_products,
        y="Product Name",
        x="Total_Profit",
        hue="Division",
        dodge=False,
        ax=ax,
        palette="Set2"
    )
    ax.set_title("Top 20 Products by Total Profit")
    ax.set_xlabel("Total Profit ($)")
    ax.set_ylabel("Product Name")
    ax.xaxis.set_major_formatter(FuncFormatter(currency_fmt))
    ax.legend(title="Division", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.bar_label(ax.containers[0], fmt='${:,.0f}', padding=3)

    st.pyplot(fig)

# -----------------------------
# PAGE: Division Performance
# -----------------------------
def page_division_performance():
    st.title("🏭 Division Performance Analysis")

    division_perf = (
        filtered_df.groupby("Division", as_index=False)
        .agg(
            Revenue=("Sales", "sum"),
            Profit=("Gross Profit", "sum"),
            Avg_Margin=("Gross Margin %", "mean")
        )
    )

    # Sort divisions descending by Revenue
    division_perf = division_perf.sort_values("Revenue", ascending=False)

    # Barplot: Revenue & Profit side-by-side bars
    fig, ax = plt.subplots(figsize=(10,6))
    width = 0.4
    x = np.arange(len(division_perf))

    ax.bar(x - width/2, division_perf["Revenue"], width=width, label="Revenue", color=sns.color_palette("Set2")[0])
    ax.bar(x + width/2, division_perf["Profit"], width=width, label="Profit", color=sns.color_palette("Set2")[2])
    ax.set_xticks(x)
    ax.set_xticklabels(division_perf["Division"], rotation=45, ha="right")
    ax.set_ylabel("Amount ($)")
    ax.set_title("Revenue vs Profit by Division")
    ax.legend()
    ax.yaxis.set_major_formatter(FuncFormatter(currency_fmt))
    for i, v in enumerate(division_perf["Revenue"]):
        ax.text(i - width/2, v + max(division_perf["Revenue"]) * 0.01, f"${v:,.0f}", ha="center", fontsize=8)
    for i, v in enumerate(division_perf["Profit"]):
        ax.text(i + width/2, v + max(division_perf["Profit"]) * 0.01, f"${v:,.0f}", ha="center", fontsize=8)

    st.pyplot(fig)

    # Boxplot for margin distribution by division
    st.markdown("### Margin Distribution by Division")
    fig2, ax2 = plt.subplots(figsize=(10,6))
    sns.boxplot(
        data=filtered_df,
        x="Division",
        y="Gross Margin %",
        palette="Set2",
        ax=ax2
    )
    ax2.set_ylabel("Gross Margin")
    ax2.set_xlabel("Division")
    ax2.set_title("Gross Margin Distribution by Division")
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x*100:.1f}%"))

    st.pyplot(fig2)

# -----------------------------
# PAGE: Cost & Margin Diagnostics
# -----------------------------
def page_cost_margin_diagnostics():
    st.title("⚠️ Cost vs Margin Diagnostics")

    fig, ax = plt.subplots(figsize=(10,7))
    scatter = sns.scatterplot(
        data=filtered_df,
        x="Cost",
        y="Gross Margin %",
        hue="Division",
        size="Units",
        sizes=(20, 200),
        alpha=0.6,
        palette="Set2",
        edgecolor="k",
        ax=ax
    )
    ax.axhline(0.20, color='red', linestyle='--', label="20% Margin Threshold")
    ax.set_xlabel("Cost ($)")
    ax.set_ylabel("Gross Margin")
    ax.set_title("Cost vs Gross Margin by Product")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    ax.xaxis.set_major_formatter(FuncFormatter(currency_fmt))
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # Annotate few key margin risk products (lowest margin & high cost)
    risk_zone = filtered_df[(filtered_df["Gross Margin %"] < 0.20) & (filtered_df["Cost"] > filtered_df["Cost"].median())]
    risk_zone = risk_zone.sort_values("Gross Margin %").head(5)
    for _, row in risk_zone.iterrows():
        ax.text(row["Cost"], row["Gross Margin %"], row["Product Name"], fontsize=8, weight="bold", color="red")

    st.pyplot(fig)

# -----------------------------
# PAGE: Pareto Analysis
# -----------------------------
def page_pareto_analysis():
    st.title("📊 Profit Concentration (Pareto Analysis)")

    pareto = product_perf.sort_values("Total_Profit", ascending=False).copy()
    pareto["Cumulative Profit %"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum()

    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(
        pareto.index + 1,
        pareto["Cumulative Profit %"],
        marker='o',
        linestyle='-',
        color=sns.color_palette("Set2")[1]
    )
    ax.axhline(0.8, color='red', linestyle='--', label="80% Profit Threshold")
    ax.set_xlabel("Number of Products (Ranked)")
    ax.set_ylabel("Cumulative Profit Contribution")
    ax.set_title("Cumulative Profit Contribution by Products")
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True)

    # Annotate the point closest to 80% cumulative profit
    closest_idx = pareto["Cumulative Profit %"].sub(0.8).abs().idxmin()
    x_annot = closest_idx + 1
    y_annot = pareto.loc[closest_idx, "Cumulative Profit %"]
    ax.annotate(f"{x_annot} products\n{y_annot:.0%} profit",
                xy=(x_annot, y_annot),
                xytext=(x_annot + 10, y_annot - 0.1),
                arrowprops=dict(facecolor='black', arrowstyle='->'),
                fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))

    st.pyplot(fig)

# -----------------------------
# MAIN PAGE LOGIC
# -----------------------------
if page == "Overview":
    page_overview()
elif page == "Product Profitability":
    page_product_profitability()
elif page == "Division Performance":
    page_division_performance()
elif page == "Cost & Margin Diagnostics":
    page_cost_margin_diagnostics()
elif page == "Pareto Analysis":
    page_pareto_analysis()

# -----------------------------
# DOWNLOAD FILTERED DATA
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.download_button(
    label="Download Filtered Data (CSV)",
    data=filtered_df.to_csv(index=False),
    file_name="nassau_candy_filtered_data.csv",
    mime="text/csv"
)

st.caption("Built for strategic profitability decision-making at Nassau Candy Distributor")
