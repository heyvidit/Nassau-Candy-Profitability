import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Profit Intelligence Dashboard",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# GLOBAL STYLE + COMPANY HEADER
# ------------------------------------------------
st.markdown("""
<style>
.company-header {
    width:100%;
    display:flex;
    justify-content:center;
    align-items:center;
    margin-top:-15px;
    border-bottom:1px solid #222;
    margin-bottom:2rem;
}
.company-logo {
    min-width:10rem;
    height:4rem;
}
</style>
""", unsafe_allow_html=True)

def add_company_header():
    try:
        with open("logo.png", "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode()

        header_html = f"""
        <div class="company-header">
            <img src="data:image/png;base64,{encoded_logo}" class="company-logo">
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    except:
        pass

add_company_header()

# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():

    df = pd.read_csv("Nassau Candy Distributor (1).csv")

    df = df.drop_duplicates(subset=["Order ID", "Product ID"])
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df = df.dropna(subset=["Sales", "Units", "Gross Profit", "Cost"])

    df["Division"] = df["Division"].str.strip()
    df["Product Name"] = df["Product Name"].str.strip()

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

    df["Calculated Profit"] = df["Sales"] - df["Cost"]
    df["Profit Mismatch"] = df["Gross Profit"] - df["Calculated Profit"]

    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]

    return df

df = load_data()

# 🔎 Audit Check
if abs(df["Profit Mismatch"]).sum() > 1:
    st.warning("⚠ Profit mismatch detected between reported and calculated profit values.")

# ------------------------------------------------
# FACTORY MAPPING
# ------------------------------------------------
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

factory_coords = {
    "Lot's O' Nuts": [32.881893, -111.768036],
    "Wicked Choccy's": [32.076176, -81.088371],
    "Sugar Shack": [48.11914, -96.18115],
    "Secret Factory": [41.446333, -90.565487],
    "The Other Factory": [35.1175, -89.971107]
}

df["Factory"] = df["Product Name"].map(factory_map)

# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------
st.sidebar.title("🔎 Filters")

division_filter = st.sidebar.multiselect(
    "Division",
    df["Division"].unique(),
    default=df["Division"].unique()
)

product_search = st.sidebar.text_input("Search Product")

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(df["Order Date"].min(), df["Order Date"].max())
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
        "Factory-Product Map",
        "Strategic Recommendations"
    ]
)

# ------------------------------------------------
# FILTER DATA
# ------------------------------------------------
filtered_df = df[
    (df["Division"].isin(division_filter)) &
    (df["Order Date"] >= pd.to_datetime(date_range[0])) &
    (df["Order Date"] <= pd.to_datetime(date_range[1])) &
    (df["Gross Margin %"] * 100 >= margin_threshold)
].copy()

if product_search:
    filtered_df = filtered_df[
        filtered_df["Product Name"].str.contains(product_search, case=False)
    ]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ------------------------------------------------
# AGGREGATION (FIXED MARGIN CALCULATION)
# ------------------------------------------------
product_perf = (
    filtered_df
    .groupby(["Division", "Product Name", "Factory"], observed=True)
    .agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum")
    )
    .reset_index()
)

# ✅ Correct Margin Calculation
product_perf["True_Margin"] = product_perf["Total_Profit"] / product_perf["Total_Sales"]
product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]

total_sales = product_perf["Total_Sales"].sum()
total_profit = product_perf["Total_Profit"].sum()

product_perf["Revenue Contribution %"] = product_perf["Total_Sales"] / total_sales * 100
product_perf["Profit Contribution %"] = product_perf["Total_Profit"] / total_profit * 100

sales_median = product_perf["Total_Sales"].median()
margin_median = product_perf["True_Margin"].median()

def classify(row):
    if row["Total_Sales"] > sales_median and row["True_Margin"] > margin_median:
        return "Star Performer"
    elif row["Total_Sales"] > sales_median:
        return "Volume Driver - Margin Risk"
    elif row["True_Margin"] > margin_median:
        return "Niche High Margin"
    else:
        return "Low Performer"

product_perf["Category"] = product_perf.apply(classify, axis=1)

# Volatility
filtered_df["Month"] = filtered_df["Order Date"].dt.to_period("M")
volatility = (
    filtered_df.groupby(["Product Name", "Month"])["Gross Margin %"]
    .mean()
    .groupby("Product Name")
    .std()
    .reset_index(name="Margin Volatility")
)

product_perf = product_perf.merge(volatility, on="Product Name", how="left")

# ------------------------------------------------
# PAGES
# ------------------------------------------------
def executive_page():
    st.title("Executive Profit Intelligence")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_sales:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Overall Margin", f"{(total_profit/total_sales)*100:.2f}%")

    st.markdown("---")

    top10 = product_perf.sort_values("Total_Profit", ascending=False).head(10)
    fig = px.bar(top10, x="Total_Profit", y="Product Name",
                 orientation="h", color="Category",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def division_page():
    st.title("Division Performance")

    division_perf = product_perf.groupby("Division").agg(
        Revenue=("Total_Sales", "sum"),
        Profit=("Total_Profit", "sum")
    ).reset_index()

    division_perf["True_Margin"] = division_perf["Profit"] / division_perf["Revenue"]

    fig = px.bar(division_perf, x="Division",
                 y=["Revenue", "Profit"],
                 barmode="group",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(division_perf)

def pareto_page():
    st.title("Profit Concentration (Pareto)")

    pareto = product_perf.sort_values("Total_Profit", ascending=False)
    pareto["Cumulative %"] = pareto["Total_Profit"].cumsum() / total_profit * 100

    fig = go.Figure()
    fig.add_bar(x=pareto["Product Name"], y=pareto["Total_Profit"], name="Profit")
    fig.add_scatter(x=pareto["Product Name"], y=pareto["Cumulative %"],
                    name="Cumulative %",
                    yaxis="y2")

    fig.update_layout(yaxis2=dict(overlaying='y', side='right'),
                      template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    top_5_ratio = pareto.head(5)["Total_Profit"].sum() / total_profit * 100
    st.info(f"Top 5 products contribute {top_5_ratio:.2f}% of total profit.")

def recommendation_page():
    st.title("Strategic Recommendations")

    low_margin = product_perf[product_perf["True_Margin"] < 0.10]

    impact_revenue = low_margin["Total_Sales"].sum()
    impact_profit = low_margin["Total_Profit"].sum()

    st.subheader("Low Margin Products (<10%)")
    st.dataframe(low_margin)

    st.info(
        f"These products generate ${impact_revenue:,.0f} revenue but only "
        f"${impact_profit:,.0f} profit. Reviewing pricing or cost structure "
        f"could materially improve overall margins."
    )

# ------------------------------------------------
# ROUTING
# ------------------------------------------------
if page == "Executive Intelligence":
    executive_page()
elif page == "Division & Factory Performance":
    division_page()
elif page == "Profit Concentration Analysis":
    pareto_page()
elif page == "Strategic Recommendations":
    recommendation_page()
    add_footer()

