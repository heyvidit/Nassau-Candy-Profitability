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
# GLOBAL STYLE
# ------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 1400px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# LOAD LOGO
# ------------------------------------------------
try:
    logo = Image.open("logo.png")
except:
    logo = None

# ------------------------------------------------
# DISPLAY LOGO + TITLE (already works on all pages)
# ------------------------------------------------
col1, col2 = st.columns([1,6])
with col1:
    if logo:
        st.image(logo, width=120)
with col2:
    st.markdown("<h1 style='margin-bottom:0;'>Profit Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:gray; margin-top:0;'>Nassau Candy Distributor</p>", unsafe_allow_html=True)

# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")

    df = df.drop_duplicates(subset=["Order ID", "Product ID"])
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df = df.dropna(subset=["Sales", "Units", "Gross Profit", "Cost"])

    df["Division"] = df["Division"].str.strip()
    df["Product Name"] = df["Product Name"].str.strip()
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]

    df["Calculated Profit"] = df["Sales"] - df["Cost"]
    df["Profit Mismatch"] = df["Gross Profit"] - df["Calculated Profit"]

    return df

df = load_data()

# ------------------------------------------------
# DATA VALIDATION MESSAGE
# ------------------------------------------------
mismatch_count = df[df["Profit Mismatch"].abs() > 0.01].shape[0]
if mismatch_count > 0:
    st.info(
        f"{mismatch_count} rows show minor rounding differences "
        "between Gross Profit and (Sales - Cost)."
    )

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
    (df["Order Date"] <= pd.to_datetime(date_range[1]))
].copy()

if product_search:
    filtered_df = filtered_df[
        filtered_df["Product Name"].str.contains(product_search, case=False)
    ]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ------------------------------------------------
# AGGREGATION
# ------------------------------------------------
product_perf = (
    filtered_df
    .groupby(["Division", "Product Name", "Factory"], observed=True)
    .agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Avg_Margin=("Gross Margin %", "mean"),
        Total_Cost=("Cost", "sum")
    )
    .reset_index()
)

product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]
product_perf["Cost Ratio %"] = product_perf["Total_Cost"] / product_perf["Total_Sales"]

# Apply margin threshold after aggregation
product_perf = product_perf[product_perf["Avg_Margin"] * 100 >= margin_threshold]

total_sales = product_perf["Total_Sales"].sum()
total_profit = product_perf["Total_Profit"].sum()

product_perf["Revenue Contribution %"] = product_perf["Total_Sales"] / total_sales * 100
product_perf["Profit Contribution %"] = product_perf["Total_Profit"] / total_profit * 100

# ------------------------------------------------
# CLASSIFICATION
# ------------------------------------------------
sales_median = product_perf["Total_Sales"].median()
margin_median = product_perf["Avg_Margin"].median()

def classify(row):
    if row["Total_Sales"] > sales_median and row["Avg_Margin"] > margin_median:
        return "Star Performer"
    elif row["Total_Sales"] > sales_median:
        return "Volume Driver - Margin Risk"
    elif row["Avg_Margin"] > margin_median:
        return "Niche High Margin"
    else:
        return "Low Performer"

product_perf["Category"] = product_perf.apply(classify, axis=1)

# ------------------------------------------------
# VOLATILITY
# ------------------------------------------------
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
# PAGE FUNCTIONS
# ------------------------------------------------
def executive_page():
    st.title("Executive Profit Intelligence")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_sales:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Average Margin", f"{product_perf['Avg_Margin'].mean()*100:.2f}%")
    st.markdown("---")
    top10 = product_perf.sort_values("Total_Profit", ascending=False).head(10)
    fig = px.bar(top10, x="Total_Profit", y="Product Name",
                 orientation="h", color="Category", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def product_portfolio_page():
    st.title("Product Portfolio Analysis")
    fig = px.scatter(product_perf,
                     x="Total_Sales",
                     y="Total_Profit",
                     size="Total_Units",
                     color="Category",
                     hover_data=["Avg_Margin", "Margin Volatility"],
                     template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def division_page():
    st.title("Division Performance")
    division_perf = product_perf.groupby("Division").agg(
        Revenue=("Total_Sales", "sum"),
        Profit=("Total_Profit", "sum"),
        Avg_Margin=("Avg_Margin", "mean")
    ).reset_index()
    division_perf["Revenue %"] = division_perf["Revenue"] / total_sales
    division_perf["Profit %"] = division_perf["Profit"] / total_profit
    division_perf["Efficiency Ratio"] = division_perf["Profit %"] / division_perf["Revenue %"]
    fig = px.bar(division_perf, x="Division",
                 y=["Revenue", "Profit"],
                 barmode="group", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(division_perf)

def cost_margin_page():
    st.title("Cost & Margin Diagnostics")
    fig = px.scatter(product_perf,
                     x="Total_Cost",
                     y="Total_Sales",
                     color="Division",
                     template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Top 10 Cost-Heavy Products")
    high_cost = product_perf.sort_values("Cost Ratio %", ascending=False).head(10)
    st.dataframe(high_cost[["Product Name", "Division", "Cost Ratio %", "Avg_Margin"]])

def pareto_page():
    st.title("Profit & Revenue Concentration (Pareto)")
    pareto = product_perf.sort_values("Total_Profit", ascending=False).copy()
    pareto["Profit Cumulative %"] = pareto["Total_Profit"].cumsum() / total_profit * 100
    pareto["Revenue Cumulative %"] = pareto["Total_Sales"].cumsum() / total_sales * 100
    fig = go.Figure()
    fig.add_bar(x=pareto["Product Name"], y=pareto["Total_Profit"], name="Profit")
    fig.add_scatter(x=pareto["Product Name"], y=pareto["Profit Cumulative %"],
                    name="Profit Cumulative %", yaxis="y2")
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    count_profit_80 = pareto[pareto["Profit Cumulative %"] <= 80].shape[0]
    count_revenue_80 = pareto[pareto["Revenue Cumulative %"] <= 80].shape[0]
    st.info(f"{count_profit_80} products contribute to 80% of total profit.")
    st.info(f"{count_revenue_80} products contribute to 80% of total revenue.")

def factory_map_page():
    st.title("Factory-Product Geographic Map")
    map_data = product_perf.groupby("Factory").agg(
        Revenue=("Total_Sales", "sum"),
        Profit=("Total_Profit", "sum")
    ).reset_index()
    map_data["Latitude"] = map_data["Factory"].map(lambda x: factory_coords[x][0])
    map_data["Longitude"] = map_data["Factory"].map(lambda x: factory_coords[x][1])
    map_data["Factory Margin"] = map_data["Profit"] / map_data["Revenue"]
    fig = px.scatter_mapbox(map_data,
                            lat="Latitude", lon="Longitude",
                            size="Revenue", color="Factory Margin",
                            hover_name="Factory", zoom=3,
                            mapbox_style="carto-darkmatter")
    st.plotly_chart(fig, use_container_width=True)

def recommendation_page():
    st.title("Strategic Recommendations")
    low_margin = product_perf[product_perf["Avg_Margin"] < 0.15]
    high_volatility = product_perf[product_perf["Margin Volatility"] > product_perf["Margin Volatility"].median()]
    st.subheader("Low Margin Products (<15%)")
    st.dataframe(low_margin)
    st.subheader("High Margin Volatility Products")
    st.dataframe(high_volatility)

# ------------------------------------------------
# ROUTING
# ------------------------------------------------
if page == "Executive Intelligence":
    executive_page()
elif page == "Product Portfolio Analysis":
    product_portfolio_page()
elif page == "Division & Factory Performance":
    division_page()
elif page == "Cost & Margin Diagnostics":
    cost_margin_page()
elif page == "Profit Concentration Analysis":
    pareto_page()
elif page == "Factory-Product Map":
    factory_map_page()
elif page == "Strategic Recommendations":
    recommendation_page()

# ------------------------------------------------
# FOOTER (UNCHANGED)
# ------------------------------------------------
def add_footer():
    try:
        with open("unified logo.png", "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode()
        footer_html = f"""
        <div class='footer' style='display:flex; justify-content:space-between; align-items:center; padding:20px 40px; background-color:#0E1117; color:#ffffff; font-size:13px; font-family:Arial, sans-serif;'>
            <div style='display:flex; align-items:center; gap:10px;'>
                <img src='data:image/png;base64,{encoded_logo}' alt='Unified Logo' style='height:50px; width:auto'>
                <span>Mentored by <a href='https://www.linkedin.com/in/saiprasad-kagne/' target='_blank' style='color:#0A66C2; text-decoration:none;'>Sai Prasad Kagne</a></span>
            </div>
            <div>
                <span>Created by <a href='https://www.linkedin.com/in/vidit-kapoor-5062b02a6' target='_blank' style='color:#0A66C2; text-decoration:none;'>Vidit Kapoor</a></span>
            </div>
            <div>
                <span>Version 1.0 | Last updated: Feb 2026</span>
            </div>
        </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)
    except:
        pass

add_footer()
