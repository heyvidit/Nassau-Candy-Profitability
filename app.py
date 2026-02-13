import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sns.set_style("whitegrid")
sns.set_palette("Set2")

st.set_page_config(page_title="Nassau Candy | Profit Intelligence System", layout="wide")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    df["Revenue Contribution"] = df["Sales"] / df["Sales"].sum()
    df["Profit Contribution"] = df["Gross Profit"] / df["Gross Profit"].sum()
    return df

df = load_data()

# -------------------------------------------------
# FACTORY MAPPING
# -------------------------------------------------
factory_map = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory"
}

df["Factory"] = df["Product Name"].map(factory_map)

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
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
    0, 100, 0
)

page = st.sidebar.radio(
    "Select Page",
    [
        "Executive Intelligence",
        "Product Portfolio Analysis",
        "Division & Factory Performance",
        "Cost & Margin Diagnostics",
        "Profit Concentration Analysis",
        "Strategic Recommendations"
    ]
)

filtered_df = df[
    (df["Division"].isin(division_filter)) &
    (df["Order Date"] >= pd.to_datetime(date_range[0])) &
    (df["Order Date"] <= pd.to_datetime(date_range[1])) &
    (df["Gross Margin %"] * 100 >= margin_threshold)
]

# -------------------------------------------------
# PRODUCT AGGREGATION
# -------------------------------------------------
product_perf = (
    filtered_df.groupby(["Division", "Product Name", "Factory"], as_index=False)
    .agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Avg_Margin=("Gross Margin %", "mean")
    )
)

product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]

# Strategic Classification
profit_median = product_perf["Total_Profit"].median()
margin_median = product_perf["Avg_Margin"].median()

def classify(row):
    if row["Total_Profit"] >= profit_median and row["Avg_Margin"] >= margin_median:
        return "Strategic Core"
    elif row["Total_Profit"] >= profit_median and row["Avg_Margin"] < margin_median:
        return "Volume Illusion"
    elif row["Total_Profit"] < profit_median and row["Avg_Margin"] < margin_median:
        return "Rationalization Candidate"
    else:
        return "Margin Risk"

product_perf["Strategic Category"] = product_perf.apply(classify, axis=1)

# -------------------------------------------------
# EXECUTIVE PAGE
# -------------------------------------------------
def executive_page():
    st.title("Executive Profit Intelligence")

    total_revenue = filtered_df["Sales"].sum()
    total_profit = filtered_df["Gross Profit"].sum()
    avg_margin = filtered_df["Gross Margin %"].mean() * 100

    top5_profit_share = (
        product_perf.sort_values("Total_Profit", ascending=False)
        .head(5)["Total_Profit"].sum() / total_profit
    ) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Avg Margin", f"{avg_margin:.2f}%")
    col4.metric("Top 5 Profit Share", f"{top5_profit_share:.1f}%")

# -------------------------------------------------
# PARETO PAGE
# -------------------------------------------------
def pareto_page():
    st.title("Profit & Revenue Concentration")

    pareto = product_perf.sort_values("Total_Profit", ascending=False).copy()
    pareto["Cumulative Profit %"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum()

    pareto_rev = product_perf.sort_values("Total_Sales", ascending=False).copy()
    pareto_rev["Cumulative Revenue %"] = pareto_rev["Total_Sales"].cumsum() / pareto_rev["Total_Sales"].sum()

    st.subheader("Profit Concentration")
    st.line_chart(pareto["Cumulative Profit %"])

    st.subheader("Revenue Concentration")
    st.line_chart(pareto_rev["Cumulative Revenue %"])

# -------------------------------------------------
# MARGIN VOLATILITY
# -------------------------------------------------
def margin_volatility():
    st.subheader("Margin Volatility Over Time")
    monthly = filtered_df.resample("M", on="Order Date")["Gross Margin %"].mean()
    st.line_chart(monthly)

# -------------------------------------------------
# FACTORY PERFORMANCE
# -------------------------------------------------
def division_factory_page():
    st.title("Division & Factory Performance")

    factory_perf = (
        product_perf.groupby("Factory", as_index=False)
        .agg(
            Revenue=("Total_Sales", "sum"),
            Profit=("Total_Profit", "sum"),
            Avg_Margin=("Avg_Margin", "mean")
        )
    )

    st.dataframe(factory_perf)

# -------------------------------------------------
# RECOMMENDATIONS
# -------------------------------------------------
def recommendation_page():
    st.title("Strategic Recommendations")

    low_margin = product_perf[product_perf["Avg_Margin"] < 0.15]
    concentration = (
        product_perf.sort_values("Total_Profit", ascending=False)
        .head(10)["Total_Profit"].sum() /
        product_perf["Total_Profit"].sum()
    ) * 100

    st.markdown(f"""
    **Key Strategic Insights:**
    
    - {len(low_margin)} products operate below 15% margin and require pricing review.
    - Top 10 products contribute {concentration:.1f}% of total profit, indicating concentration risk.
    - Strategic Core products should be protected and prioritized.
    - Volume Illusion products require margin improvement strategies.
    """)

# -------------------------------------------------
# PAGE ROUTING
# -------------------------------------------------
if page == "Executive Intelligence":
    executive_page()
elif page == "Product Portfolio Analysis":
    st.dataframe(product_perf)
    margin_volatility()
elif page == "Division & Factory Performance":
    division_factory_page()
elif page == "Cost & Margin Diagnostics":
    st.scatter_chart(filtered_df[["Cost", "Gross Margin %"]])
elif page == "Profit Concentration Analysis":
    pareto_page()
elif page == "Strategic Recommendations":
    recommendation_page()
