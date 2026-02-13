import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="Nassau Candy | Profit Intelligence",
    page_icon="🍬",
    layout="wide"
)

# ------------------------------
# LOAD DATA
# ------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")

    # Remove invalid records
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df = df.dropna(subset=["Sales", "Units", "Gross Profit", "Cost"])

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

    # Safe metric calculations
    df["Gross Margin %"] = np.where(df["Sales"] != 0, df["Gross Profit"] / df["Sales"], 0)
    df["Profit per Unit"] = np.where(df["Units"] != 0, df["Gross Profit"] / df["Units"], 0)

    return df

df = load_data()

# ------------------------------
# FACTORY MAPPING
# ------------------------------
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

factory_coords = {
    "Lot's O' Nuts": [32.881893, -111.768036],
    "Wicked Choccy's": [32.076176, -81.088371],
    "Sugar Shack": [48.11914, -96.18115],
    "Secret Factory": [41.446333, -90.565487],
    "The Other Factory": [35.1175, -89.971107]
}

# ------------------------------
# SIDEBAR FILTERS
# ------------------------------
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
        "Factory-Product Map",
        "Strategic Recommendations"
    ]
)

filtered_df = df[
    (df["Division"].isin(division_filter)) &
    (df["Order Date"] >= pd.to_datetime(date_range[0])) &
    (df["Order Date"] <= pd.to_datetime(date_range[1])) &
    (df["Gross Margin %"] * 100 >= margin_threshold)
].copy()

# Prevent crash if empty
if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ------------------------------
# PRODUCT AGGREGATION
# ------------------------------
product_perf = (
    filtered_df
    .groupby(["Division", "Product Name", "Factory"], observed=True)
    .agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Avg_Margin=("Gross Margin %", "mean"),
        Margin_Std=("Gross Margin %", "std")
    )
    .reset_index()
)

product_perf["Profit per Unit"] = np.where(
    product_perf["Total_Units"] != 0,
    product_perf["Total_Profit"] / product_perf["Total_Units"],
    0
)

# Strategic Classification
profit_median = product_perf["Total_Profit"].median()
margin_median = product_perf["Avg_Margin"].median()

def classify(row):
    if row["Total_Profit"] >= profit_median and row["Avg_Margin"] >= margin_median:
        return "Strategic Core"
    elif row["Total_Profit"] >= profit_median:
        return "Volume Illusion"
    elif row["Avg_Margin"] < margin_median:
        return "Rationalization Candidate"
    else:
        return "Margin Risk"

product_perf["Strategic Category"] = product_perf.apply(classify, axis=1)

filtered_df = filtered_df.merge(
    product_perf[["Product Name", "Strategic Category"]],
    on="Product Name",
    how="left"
)

# ------------------------------
# EXECUTIVE PAGE
# ------------------------------
def executive_page():
    st.title("Executive Profit Intelligence")

    total_revenue = filtered_df["Sales"].sum()
    total_profit = filtered_df["Gross Profit"].sum()
    avg_margin = filtered_df["Gross Margin %"].mean() * 100

    top5_profit_share = (
        product_perf.sort_values("Total_Profit", ascending=False)
        .head(5)["Total_Profit"].sum()
        / total_profit * 100
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Average Margin", f"{avg_margin:.2f}%")
    col4.metric("Top 5 Profit Share", f"{top5_profit_share:.1f}%")

# ------------------------------
# PRODUCT PORTFOLIO
# ------------------------------
def product_portfolio_analysis():
    st.title("Product Portfolio Analysis")

    fig = px.scatter(
        product_perf,
        x="Total_Sales",
        y="Total_Profit",
        color="Strategic Category",
        size="Total_Units",
        hover_data=["Product Name", "Division", "Factory", "Avg_Margin", "Margin_Std"],
        log_x=True,
        size_max=30,
        title="Sales vs Profit by Product"
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# DIVISION PERFORMANCE
# ------------------------------
def division_factory_page():
    st.title("Division Performance")

    division_perf = product_perf.groupby("Division", observed=True).agg(
        Revenue=("Total_Sales", "sum"),
        Profit=("Total_Profit", "sum")
    ).reset_index()

    fig = px.bar(
        division_perf,
        x="Division",
        y=["Revenue", "Profit"],
        barmode="group",
        text_auto=True
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# COST DIAGNOSTICS
# ------------------------------
def cost_margin_page():
    st.title("Cost vs Margin Diagnostics")

    fig = px.scatter(
        filtered_df,
        x="Cost",
        y="Gross Margin %",
        color="Strategic Category",
        hover_data=["Product Name", "Division", "Factory"],
        title="Cost vs Gross Margin"
    )

    fig.add_hline(y=margin_median, line_dash="dash")
    fig.add_vline(x=filtered_df["Cost"].median(), line_dash="dash")

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# PARETO
# ------------------------------
def profit_concentration_page():
    st.title("Profit Concentration Analysis")

    pareto = product_perf.sort_values("Total_Profit", ascending=False)
    pareto["Cumulative Profit %"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum()

    fig = px.line(
        pareto,
        y="Cumulative Profit %",
        x=range(len(pareto))
    )

    fig.add_hline(y=0.8, line_dash="dash", line_color="red")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# FACTORY MAP
# ------------------------------
def factory_map_page():
    st.title("Factory Locations")

    map_data = []

    for factory, coords in factory_coords.items():
        map_data.append({
            "Factory": factory,
            "Latitude": coords[0],
            "Longitude": coords[1]
        })

    map_df = pd.DataFrame(map_data)

    fig = px.scatter_geo(
        map_df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Factory",
        scope="usa"
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# RECOMMENDATIONS
# ------------------------------
def recommendation_page():
    st.title("Strategic Recommendations")

    low_margin = product_perf[product_perf["Avg_Margin"] < 0.15]

    st.write(f"{len(low_margin)} products operate below 15% margin.")

    st.dataframe(low_margin)

# ------------------------------
# ROUTING
# ------------------------------
if page == "Executive Intelligence":
    executive_page()
elif page == "Product Portfolio Analysis":
    product_portfolio_analysis()
elif page == "Division & Factory Performance":
    division_factory_page()
elif page == "Cost & Margin Diagnostics":
    cost_margin_page()
elif page == "Profit Concentration Analysis":
    profit_concentration_page()
elif page == "Factory-Product Map":
    factory_map_page()
elif page == "Strategic Recommendations":
    recommendation_page()
