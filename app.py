import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
from scipy import stats

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
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 0;
    margin-bottom: 2rem;
}
.company-logo {
    height: 4rem;
    width: auto;
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

    # Original Cleaning
    df = df.drop_duplicates(subset=["Order ID", "Product ID"])
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df = df.dropna(subset=["Sales", "Units", "Gross Profit", "Cost"])
    df["Division"] = df["Division"].str.strip()
    df["Product Name"] = df["Product Name"].str.strip()
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    # Profit Validation
    df["Calculated Profit"] = df["Sales"] - df["Cost"]
    df["Profit Mismatch"] = df["Gross Profit"] - df["Calculated Profit"]

    # Remove negative gross profit
    df = df[df["Gross Profit"] >= 0]

    # Ship date validation
    df = df[df["Ship Date"] >= df["Order Date"]]

    # Metrics
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    df["Cost per Unit"] = df["Cost"] / df["Units"]
    df["Avg Selling Price"] = df["Sales"] / df["Units"]

    # Outlier Detection (Z-score on margin)
    df["Margin Z-Score"] = np.abs(stats.zscore(df["Gross Margin %"]))
    df["Margin Outlier"] = df["Margin Z-Score"] > 3

    return df

df = load_data()

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
# SIDEBAR (UNCHANGED)
# ------------------------------------------------
st.sidebar.header("Analysis Controls")

st.sidebar.markdown(
    "Refine your dashboard using these controls. Focus on key products, divisions, and time periods."
)

st.sidebar.markdown(
    """
    <style>
    .stDateInput > div[data-baseweb="select"] > div:first-child {
        max-height: 7rem;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.subheader("Date & Scope")
date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(df["Order Date"].min(), df["Order Date"].max())
)
division_filter = st.sidebar.multiselect(
    "Division",
    df["Division"].unique(),
    default=df["Division"].unique()
)

st.sidebar.subheader("Product Controls")
all_products = df["Product Name"].unique().tolist()

product_search = st.sidebar.multiselect(
    "Select Products",
    options=all_products,
    default=[]
)

margin_threshold = st.sidebar.slider(
    "Margin Filter Threshold (%)",
    0, 100, 0
)

st.sidebar.subheader("Dashboard Module")
page = st.sidebar.radio(
    "",
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
    filtered_df = filtered_df[filtered_df["Product Name"].isin(product_search)]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

filtered_df["Month"] = filtered_df["Order Date"].dt.to_period("M")

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
        Total_Cost=("Cost", "sum")
    )
    .reset_index()
)

product_perf["Avg_Margin"] = product_perf["Total_Profit"] / product_perf["Total_Sales"]
product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]
product_perf["Cost per Unit"] = product_perf["Total_Cost"] / product_perf["Total_Units"]
product_perf["Avg Selling Price"] = product_perf["Total_Sales"] / product_perf["Total_Units"]

total_sales = product_perf["Total_Sales"].sum()
total_profit = product_perf["Total_Profit"].sum()

product_perf["Revenue Contribution %"] = product_perf["Total_Sales"] / total_sales * 100
product_perf["Profit Contribution %"] = product_perf["Total_Profit"] / total_profit * 100

# Division Contribution %
division_contrib = product_perf.groupby("Division").agg(
    Revenue=("Total_Sales","sum"),
    Profit=("Total_Profit","sum")
).reset_index()

division_contrib["Revenue Contribution %"] = division_contrib["Revenue"] / total_sales * 100
division_contrib["Profit Contribution %"] = division_contrib["Profit"] / total_profit * 100
division_contrib["True Margin"] = division_contrib["Profit"] / division_contrib["Revenue"]

# Division Volatility
division_volatility = (
    filtered_df.groupby(["Division","Month"])["Gross Margin %"]
    .mean()
    .groupby("Division")
    .std()
    .reset_index(name="Margin Volatility")
)

division_contrib = division_contrib.merge(division_volatility,on="Division",how="left")

# Revenue Pareto
revenue_pareto = product_perf.sort_values("Total_Sales",ascending=False)
revenue_pareto["Cumulative Revenue %"] = revenue_pareto["Total_Sales"].cumsum()/total_sales*100

# Dependency Risk
profit_pareto = product_perf.sort_values("Total_Profit",ascending=False)
profit_pareto["Cumulative Profit %"] = profit_pareto["Total_Profit"].cumsum()/total_profit*100

revenue_80_count = revenue_pareto[revenue_pareto["Cumulative Revenue %"]>=80].index.min()+1
profit_80_count = profit_pareto[profit_pareto["Cumulative Profit %"]>=80].index.min()+1

dependency_risk = "High" if profit_80_count <= 3 else "Moderate" if profit_80_count <=5 else "Low"

# Automated Margin Risk Flag
product_perf["Margin Risk Flag"] = np.where(
    product_perf["Avg_Margin"] < product_perf["Avg_Margin"].median(),
    "Risk",
    "Healthy"
)

# Factory Performance
factory_perf = product_perf.groupby("Factory").agg(
    Revenue=("Total_Sales","sum"),
    Profit=("Total_Profit","sum"),
    Avg_Margin=("Avg_Margin","mean"),
    Cost_per_Unit=("Cost per Unit","mean")
).reset_index()

# ------------------------------------------------
# EXISTING PAGES REMAIN UNCHANGED
# ------------------------------------------------
def executive_page():
    st.title("Executive Profit Intelligence")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_sales:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("True Average Margin", f"{(total_profit/total_sales)*100:.2f}%")
    st.markdown("---")

    monthly = filtered_df.groupby("Month").agg(
        Revenue=("Sales", "sum"),
        Profit=("Gross Profit", "sum")
    ).reset_index()
    monthly["Margin %"] = monthly["Profit"] / monthly["Revenue"]
    monthly["Month"] = monthly["Month"].astype(str)

    fig_trend = px.line(monthly, x="Month", y="Margin %",
                        title="Monthly Margin Trend",
                        template="plotly_dark")
    st.plotly_chart(fig_trend, use_container_width=True)

    top10 = product_perf.sort_values("Total_Profit", ascending=False).head(10)
    fig = px.bar(top10, x="Total_Profit", y="Product Name",
                 orientation="h",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def product_portfolio_page():
    st.title("Product Portfolio Analysis")
    fig = px.scatter(product_perf,
                     x="Total_Sales",
                     y="Total_Profit",
                     size="Total_Units",
                     template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def division_page():
    st.title("Division Performance")
    fig = px.bar(division_contrib, x="Division",
                 y=["Revenue","Profit"],
                 barmode="group",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(division_contrib)

def cost_margin_page():
    st.title("Cost & Margin Diagnostics")
    fig1 = px.scatter(filtered_df,
                      x="Cost",
                      y="Sales",
                      color="Division",
                      trendline="ols",
                      template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.scatter(filtered_df,
                      x="Cost",
                      y="Gross Margin %",
                      color="Division",
                      trendline="ols",
                      template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

def pareto_page():
    st.title("Profit Concentration (Pareto)")
    fig = go.Figure()
    fig.add_bar(x=profit_pareto["Product Name"], y=profit_pareto["Total_Profit"])
    fig.add_scatter(x=profit_pareto["Product Name"],
                    y=profit_pareto["Cumulative Profit %"],
                    yaxis="y2")
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'),
                      template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"{profit_80_count} products contribute to 80% of total profit.")
    st.info(f"{revenue_80_count} products contribute to 80% of total revenue.")
    st.warning(f"Dependency Risk Level: {dependency_risk}")

def factory_map_page():
    st.title("Factory-Product Geographic Map")
    map_data = factory_perf.copy()
    map_data["Latitude"] = map_data["Factory"].map(lambda x: factory_coords[x][0])
    map_data["Longitude"] = map_data["Factory"].map(lambda x: factory_coords[x][1])
    fig = px.scatter_mapbox(map_data,
                            lat="Latitude",
                            lon="Longitude",
                            size="Revenue",
                            color="Avg_Margin",
                            zoom=3,
                            mapbox_style="carto-darkmatter")
    st.plotly_chart(fig, use_container_width=True)

def recommendation_page():
    st.title("Strategic Recommendations")
    st.write("1. Reprice low-margin high-volume SKUs.")
    st.write("2. Renegotiate cost structure for high cost-per-unit factories.")
    st.write("3. Scale niche high-margin products with marketing support.")
    st.write("4. Monitor high volatility divisions for instability.")
    st.dataframe(product_perf[product_perf["Margin Risk Flag"]=="Risk"])

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
        st.markdown("Footer Error")

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

add_footer()
