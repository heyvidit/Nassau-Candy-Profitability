import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Nassau Candy | Profit Intelligence",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# GLOBAL STYLE FIX (BALANCE + WIDTH)
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
# LOAD DATA
# ------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df = df.dropna(subset=["Sales", "Units", "Gross Profit", "Cost"])
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

    df["Gross Margin %"] = np.where(df["Sales"] != 0,
                                    df["Gross Profit"] / df["Sales"], 0)
    df["Profit per Unit"] = np.where(df["Units"] != 0,
                                     df["Gross Profit"] / df["Units"], 0)
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

df["Factory"] = df["Product Name"].map(factory_map)

# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------
st.sidebar.title("🔎 Filters")

division_filter = st.sidebar.multiselect(
    "Division",
    options=df["Division"].unique(),
    default=df["Division"].unique()
)

st.sidebar.markdown("### 📅 Order Date Range")

date_range = st.sidebar.date_input(
    label="",
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

filtered_df = df[
    (df["Division"].isin(division_filter)) &
    (df["Order Date"] >= pd.to_datetime(date_range[0])) &
    (df["Order Date"] <= pd.to_datetime(date_range[1])) &
    (df["Gross Margin %"] * 100 >= margin_threshold)
].copy()

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ------------------------------------------------
# PRODUCT AGGREGATION
# ------------------------------------------------
product_perf = (
    filtered_df
    .groupby(["Division", "Product Name", "Factory"], observed=True)
    .agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Avg_Margin=("Gross Margin %", "mean")
    )
    .reset_index()
)

product_perf["Profit per Unit"] = product_perf["Total_Profit"] / product_perf["Total_Units"]

# ------------------------------------------------
# EXECUTIVE PAGE (BALANCED LAYOUT)
# ------------------------------------------------
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

    # KPI ROW
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Average Margin", f"{avg_margin:.2f}%")
    col4.metric("Top 5 Profit Share", f"{top5_profit_share:.1f}%")

    st.markdown("---")

    # Balanced Layout with plots to remove empty space
    left, right = st.columns([2, 1])

    with left:
        top_products = (
            product_perf.sort_values("Total_Profit", ascending=False)
            .head(10)
        )

        fig = px.bar(
            top_products,
            x="Total_Profit",
            y="Product Name",
            orientation="h",
            title="Top 10 Products by Profit",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        division_perf = product_perf.groupby("Division", observed=True).agg(
            Profit=("Total_Profit", "sum")
        ).reset_index()

        fig2 = px.pie(
            division_perf,
            names="Division",
            values="Profit",
            title="Profit Share by Division",
            hole=0.5
        )

        st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------
# PRODUCT PORTFOLIO ANALYSIS PAGE
# ------------------------------------------------
def product_portfolio_analysis():
    st.title("Product Portfolio Analysis")

    fig = px.scatter(
        product_perf,
        x="Total_Sales",
        y="Total_Profit",
        size="Total_Units",
        color="Division",
        hover_data=["Product Name", "Avg_Margin"],
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# DIVISION & FACTORY PERFORMANCE PAGE
# ------------------------------------------------
def division_factory_page():
    st.title("Division & Factory Performance")

    division_perf = product_perf.groupby("Division", observed=True).agg(
        Revenue=("Total_Sales", "sum"),
        Profit=("Total_Profit", "sum")
    ).reset_index()

    fig = px.bar(
        division_perf,
        x="Division",
        y=["Revenue", "Profit"],
        barmode="group",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# COST & MARGIN DIAGNOSTICS PAGE
# ------------------------------------------------
def cost_margin_page():
    st.title("Cost & Margin Diagnostics")

    fig = px.scatter(
        filtered_df,
        x="Cost",
        y="Gross Margin %",
        color="Division",
        template="plotly_dark",
        hover_data=["Product Name"]
    )

    fig.add_hline(y=filtered_df["Gross Margin %"].median(), line_dash="dash")

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# PROFIT CONCENTRATION ANALYSIS PAGE
# ------------------------------------------------
def profit_concentration_page():
    st.title("Profit Concentration Analysis")

    pareto = product_perf.sort_values("Total_Profit", ascending=False)
    pareto["Cumulative %"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum()

    fig = go.Figure()

    fig.add_bar(x=pareto["Product Name"], y=pareto["Total_Profit"], name="Profit")
    fig.add_scatter(x=pareto["Product Name"], y=pareto["Cumulative %"], name="Cumulative %", yaxis="y2")

    fig.update_layout(
        template="plotly_dark",
        yaxis2=dict(overlaying='y', side='right')
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# FACTORY-PRODUCT MAP PAGE (Placeholder)
# ------------------------------------------------
def factory_map_page():
    st.title("Factory-Product Map")
    st.info("Factory map visualization to be implemented.")

# ------------------------------------------------
# STRATEGIC RECOMMENDATIONS PAGE
# ------------------------------------------------
def recommendation_page():
    st.title("Strategic Recommendations")

    low_margin = product_perf[product_perf["Avg_Margin"] < 0.15]

    st.write(f"{len(low_margin)} products operate below 15% margin.")
    st.dataframe(low_margin)

# ------------------------------------------------
# PAGE ROUTING
# ------------------------------------------------
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
