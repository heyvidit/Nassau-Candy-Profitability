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
# GLOBAL STYLE + COMPANY HEADER (PRESERVED)
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

    df["Mismatch Flag"] = np.where(
        np.abs(df["Profit Mismatch"]) > (0.01 * df["Sales"]),
        True, False
    )

    df = df[df["Gross Profit"] >= 0]
    df = df[df["Ship Date"] >= df["Order Date"]]

    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    df["Cost per Unit"] = df["Cost"] / df["Units"]
    df["Avg Selling Price"] = df["Sales"] / df["Units"]

    if df["Gross Margin %"].std() != 0:
        df["Margin Z-Score"] = np.abs(stats.zscore(df["Gross Margin %"]))
    else:
        df["Margin Z-Score"] = 0

    df["Margin Outlier"] = df["Margin Z-Score"] > 3

    return df

df = load_data()

# ------------------------------------------------
# FACTORY MAPPING (FULLY RESTORED)
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
df["Factory"] = df["Factory"].fillna("Unknown Factory")

# ------------------------------------------------
# SIDEBAR (PRESERVED)
# ------------------------------------------------
st.sidebar.header("Analysis Controls")

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(df["Order Date"].min(), df["Order Date"].max())
)

division_filter = st.sidebar.multiselect(
    "Division",
    df["Division"].unique(),
    default=df["Division"].unique()
)

product_search = st.sidebar.multiselect(
    "Select Products",
    options=df["Product Name"].unique().tolist(),
    default=[]
)

margin_threshold = st.sidebar.slider(
    "Margin Filter Threshold (%)",
    0, 100, 0
)

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

total_sales = product_perf["Total_Sales"].sum()
total_profit = product_perf["Total_Profit"].sum()

if total_sales == 0:
    total_sales = 1
if total_profit == 0:
    total_profit = 1

product_perf["Avg_Margin"] = product_perf["Total_Profit"] / product_perf["Total_Sales"]
product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]
product_perf["Cost per Unit"] = product_perf["Total_Cost"] / product_perf["Total_Units"]

# Improved Risk Classification
q25 = product_perf["Avg_Margin"].quantile(0.25)
q50 = product_perf["Avg_Margin"].quantile(0.50)

def classify_margin(x):
    if x <= q25:
        return "High Risk"
    elif x <= q50:
        return "Watch"
    else:
        return "Healthy"

product_perf["Margin Risk Flag"] = product_perf["Avg_Margin"].apply(classify_margin)

# ------------------------------------------------
# FOOTER (PRESERVED)
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

add_footer()
