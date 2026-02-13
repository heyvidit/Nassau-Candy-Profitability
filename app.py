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
# LOAD & CLEAN DATA
# ------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")
    # Filter invalid records
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df.dropna(subset=["Sales","Units","Gross Profit","Cost"], inplace=True)
    
    # Convert types
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Division"] = df["Division"].astype("category")
    df["Product Name"] = df["Product Name"].astype("category")
    
    # Metrics
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"]
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    df["Revenue Contribution"] = df["Sales"] / df["Sales"].sum()
    df["Profit Contribution"] = df["Gross Profit"] / df["Gross Profit"].sum()
    
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
df["Factory"] = df["Factory"].astype("category")

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
    options=df["Division"].cat.categories.tolist(),
    default=df["Division"].cat.categories.tolist()
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
    (df["Gross Margin %"]*100 >= margin_threshold)
]

# ------------------------------
# PRODUCT AGGREGATION
# ------------------------------
product_perf = (
    filtered_df.groupby(["Division","Product Name","Factory"], as_index=False)
    .agg(
        Total_Sales=("Sales","sum"),
        Total_Profit=("Gross Profit","sum"),
        Total_Units=("Units","sum"),
        Avg_Margin=("Gross Margin %","mean"),
        Margin_Std=("Gross Margin %","std")
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
product_perf["Strategic Category"] = product_perf["Strategic Category"].astype("category")

# Merge for plotting
filtered_df = filtered_df.merge(
    product_perf[["Product Name","Strategic Category","Total_Profit","Total_Units"]],
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
    avg_margin = filtered_df["Gross Margin %"].mean()*100
    top5_profit_share = product_perf.sort_values("Total_Profit", ascending=False).head(5)["Total_Profit"].sum()/total_profit*100

    cols = st.columns(4)
    cols[0].metric("Total Revenue", f"${total_revenue:,.0f}")
    cols[1].metric("Total Profit", f"${total_profit:,.0f}")
    cols[2].metric("Avg Margin", f"{avg_margin:.2f}%")
    cols[3].metric("Top 5 Profit Share", f"{top5_profit_share:.1f}%")

# ------------------------------
# PRODUCT PORTFOLIO ANALYSIS
# ------------------------------
def product_portfolio_analysis():
    st.title("Product Portfolio Analysis")
    color_map = {
        "Strategic Core": "#2ca02c",
        "Volume Illusion": "#1f77b4",
        "Margin Risk": "#ff7f0e",
        "Rationalization Candidate": "#d62728"
    }
    fig = px.scatter(
        product_perf,
        x="Total_Sales",
        y="Total_Profit",
        color="Strategic Category",
        size="Total_Units",
        hover_data=["Product Name","Division","Factory","Avg_Margin","Margin_Std"],
        color_discrete_map=color_map,
        log_x=True,
        size_max=30,
        title="Product Performance: Sales vs Profit"
    )
    st.plotly_chart(fig, use_container_width=True)

    csv = product_perf.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Product Performance CSV",
        data=csv,
        file_name="filtered_product_performance.csv",
        mime="text/csv"
    )

# ------------------------------
# DIVISION & FACTORY PERFORMANCE
# ------------------------------
def division_factory_page():
    st.title("Division & Factory Performance")
    division_perf = product_perf.groupby("Division", as_index=False).agg(
        Revenue=("Total_Sales","sum"),
        Profit=("Total_Profit","sum"),
        Avg_Margin=("Avg_Margin","mean")
    )
    fig = px.bar(
        division_perf,
        x="Division",
        y=["Revenue","Profit"],
        barmode="group",
        text_auto=True,
        title="Revenue vs Profit by Division"
    )
    st.plotly_chart(fig, use_container_width=True)

    factory_perf = product_perf.groupby("Factory", as_index=False).agg(
        Revenue=("Total_Sales","sum"),
        Profit=("Total_Profit","sum"),
        Avg_Margin=("Avg_Margin","mean")
    )
    fig2 = px.bar(
        factory_perf,
        x="Factory",
        y=["Revenue","Profit"],
        barmode="group",
        text_auto=True,
        title="Revenue vs Profit by Factory"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------
# COST VS MARGIN DIAGNOSTICS
# ------------------------------
def cost_margin_page():
    st.title("Cost vs Margin Diagnostics")
    plot_df = filtered_df.dropna(subset=["Cost","Gross Margin %","Total_Units"])
    color_map = {
        "Strategic Core":"#2ca02c",
        "Volume Illusion":"#1f77b4",
        "Margin Risk":"#ff7f0e",
        "Rationalization Candidate":"#d62728"
    }
    fig = px.scatter(
        plot_df,
        x="Cost",
        y="Gross Margin %",
        color="Strategic Category",
        size="Total_Units",
        hover_data=["Product Name","Division","Factory","Total_Profit","Avg_Margin"],
        color_discrete_map=color_map,
        size_max=30,
        title="Cost vs Gross Margin"
    )
    # Quadrant lines
    fig.add_hline(y=margin_median, line_dash="dash", line_color="black", annotation_text="Median Margin")
    fig.add_vline(x=plot_df["Cost"].median(), line_dash="dash", line_color="black", annotation_text="Median Cost")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# PROFIT & REVENUE CONCENTRATION
# ------------------------------
def profit_concentration_page():
    st.title("Profit & Revenue Concentration")
    pareto_profit = product_perf.sort_values("Total_Profit", ascending=False)
    pareto_profit["Cumulative Profit %"] = pareto_profit["Total_Profit"].cumsum()/pareto_profit["Total_Profit"].sum()
    fig = px.line(
        pareto_profit,
        y="Cumulative Profit %",
        x=range(len(pareto_profit)),
        title="Cumulative Profit Concentration"
    )
    fig.add_hline(y=0.8, line_dash="dash", line_color="red", annotation_text="80% Threshold")
    st.plotly_chart(fig, use_container_width=True)

    # Revenue Pareto
    pareto_revenue = product_perf.sort_values("Total_Sales", ascending=False)
    pareto_revenue["Cumulative Revenue %"] = pareto_revenue["Total_Sales"].cumsum()/pareto_revenue["Total_Sales"].sum()
    fig2 = px.line(
        pareto_revenue,
        y="Cumulative Revenue %",
        x=range(len(pareto_revenue)),
        title="Cumulative Revenue Concentration"
    )
    fig2.add_hline(y=0.8, line_dash="dash", line_color="red", annotation_text="80% Threshold")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------
# FACTORY-PRODUCT MAP
# ------------------------------
def factory_map_page():
    st.title("Factory-Product Distribution Map")
    map_data = []
    for factory, coords in factory_coords.items():
        products = product_perf[product_perf["Factory"]==factory]["Product Name"].unique()
        map_data.append({
            "Factory": factory,
            "Latitude": coords[0],
            "Longitude": coords[1],
            "Products": ", ".join(products),
            "Product_Count": len(products)
        })
    map_df = pd.DataFrame(map_data)
    fig = px.scatter_geo(
        map_df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Factory",
        hover_data=["Products","Product_Count"],
        size="Product_Count",
        scope="usa",
        color="Factory",
        title="Factory Locations and Products"
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# STRATEGIC RECOMMENDATIONS
# ------------------------------
def recommendation_page():
    st.title("Strategic Recommendations")
    low_margin = product_perf[product_perf["Avg_Margin"] < 0.15]
    top10_profit_contribution = product_perf.sort_values("Total_Profit", ascending=False).head(10)["Total_Profit"].sum()/product_perf["Total_Profit"].sum()*100
    st.markdown(f"""
    **Key Strategic Insights:**
    - {len(low_margin)} products operate below 15% margin and require pricing review.
    - Top 10 products contribute {top10_profit_contribution:.1f}% of total profit, indicating concentration risk.
    - Strategic Core products should be protected and prioritized.
    - Volume Illusion products require margin improvement strategies.
    """)
    if not low_margin.empty:
        st.subheader("Low-Margin Products (<15%)")
        st.dataframe(low_margin[["Product Name","Division","Factory","Avg_Margin","Total_Profit","Strategic Category"]])

# ------------------------------
# PAGE ROUTING
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
