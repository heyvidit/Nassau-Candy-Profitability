import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Nassau Candy | Profit Intelligence System", layout="wide", page_icon="🍬")

# ---------------------------
# LOAD DATA
# ---------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor (1).csv")
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df.dropna(subset=["Sales", "Units", "Gross Profit", "Cost"], inplace=True)
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"] * 100
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    df["Revenue Contribution"] = df["Sales"] / df["Sales"].sum()
    df["Profit Contribution"] = df["Gross Profit"] / df["Gross Profit"].sum()
    return df

df = load_data()

# ---------------------------
# FACTORY MAPPING
# ---------------------------
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

# ---------------------------
# SIDEBAR FILTERS
# ---------------------------
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
    (df["Gross Margin %"] >= margin_threshold)
]

# ---------------------------
# PRODUCT AGGREGATION
# ---------------------------
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

# Strategic Classification using vectorized np.select
profit_median = product_perf["Total_Profit"].median()
margin_median = product_perf["Avg_Margin"].median()

conditions = [
    (product_perf["Total_Profit"] >= profit_median) & (product_perf["Avg_Margin"] >= margin_median),
    (product_perf["Total_Profit"] >= profit_median) & (product_perf["Avg_Margin"] < margin_median),
    (product_perf["Total_Profit"] < profit_median) & (product_perf["Avg_Margin"] < margin_median)
]
choices = ["Strategic Core", "Volume Illusion", "Rationalization Candidate"]
product_perf["Strategic Category"] = np.select(conditions, choices, default="Margin Risk")

# Merge strategic category for easy plotting
filtered_df = filtered_df.merge(
    product_perf[["Product Name", "Strategic Category"]],
    on="Product Name",
    how="left"
)

# ---------------------------
# EXECUTIVE DASHBOARD
# ---------------------------
def executive_page():
    st.title("Executive Profit Intelligence")

    total_revenue = filtered_df["Sales"].sum()
    total_profit = filtered_df["Gross Profit"].sum()
    avg_margin = filtered_df["Gross Margin %"].mean()

    category_summary = product_perf.groupby("Strategic Category").agg(
        Revenue=("Total_Sales", "sum"),
        Profit=("Total_Profit", "sum"),
        Count=("Product Name", "nunique")
    ).reset_index()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Avg Margin", f"{avg_margin:.2f}%")
    top5_profit_share = (
        product_perf.sort_values("Total_Profit", ascending=False)
        .head(5)["Total_Profit"].sum() / total_profit * 100
    )
    col4.metric("Top 5 Profit Share", f"{top5_profit_share:.1f}%")

    st.subheader("Strategic Category Overview")
    fig = px.bar(
        category_summary,
        x="Strategic Category",
        y="Profit",
        color="Strategic Category",
        text="Profit",
        color_discrete_map={
            "Strategic Core":"#2ca02c",
            "Volume Illusion":"#1f77b4",
            "Margin Risk":"#ff7f0e",
            "Rationalization Candidate":"#d62728"
        }
    )
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                      xaxis_title="", yaxis_title="Profit USD")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# PRODUCT PORTFOLIO PAGE
# ---------------------------
def product_portfolio_analysis():
    st.title("Product Portfolio Analysis")
    # Color-coded table
    color_map = {
        "Strategic Core": "#2ca02c",
        "Volume Illusion": "#1f77b4",
        "Margin Risk": "#ff7f0e",
        "Rationalization Candidate": "#d62728"
    }
    styled_df = product_perf.style.apply(lambda x: [f"background-color: {color_map.get(x['Strategic Category'],'')}; color:white"]*len(x), axis=1)
    st.dataframe(styled_df)
    # Download
    csv = product_perf.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "filtered_product_performance.csv", "text/csv")

    # Margin volatility
    st.subheader("Margin Volatility Over Time")
    monthly = filtered_df.resample("M", on="Order Date")["Gross Margin %"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly.index, y=monthly.values, mode='lines+markers', name="Avg Margin"))
    fig.update_layout(xaxis_title="Month", yaxis_title="Gross Margin %", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# DIVISION & FACTORY PERFORMANCE
# ---------------------------
def division_factory_page():
    st.title("Division & Factory Performance")

    # Division
    division_perf = product_perf.groupby("Division").agg(
        Revenue=("Total_Sales","sum"),
        Profit=("Total_Profit","sum"),
        Avg_Margin=("Avg_Margin","mean")
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=division_perf['Division'], y=division_perf['Revenue'], name="Revenue", marker_color="#1f77b4"))
    fig.add_trace(go.Bar(x=division_perf['Division'], y=division_perf['Profit'], name="Profit", marker_color="#2ca02c"))
    fig.update_layout(barmode='group', xaxis_title="Division", yaxis_title="USD", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(division_perf)

    # Factory
    factory_perf = product_perf.groupby("Factory").agg(
        Revenue=("Total_Sales","sum"),
        Profit=("Total_Profit","sum"),
        Avg_Margin=("Avg_Margin","mean")
    ).reset_index()
    st.subheader("Factory Performance")
    st.dataframe(factory_perf)

# ---------------------------
# COST VS MARGIN DIAGNOSTICS
# ---------------------------
def cost_margin_page():
    st.title("Cost vs Margin Diagnostics")
    fig = px.scatter(
        filtered_df,
        x="Cost",
        y="Gross Margin %",
        color="Strategic Category",
        hover_data=["Product Name", "Division", "Factory", "Total_Profit"],
        color_discrete_map={
            "Strategic Core":"#2ca02c",
            "Volume Illusion":"#1f77b4",
            "Margin Risk":"#ff7f0e",
            "Rationalization Candidate":"#d62728"
        },
        size="Units",
        opacity=0.7
    )
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Cost", yaxis_title="Gross Margin %")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# PROFIT CONCENTRATION (Pareto)
# ---------------------------
def pareto_page():
    st.title("Profit & Revenue Concentration")
    pareto = product_perf.sort_values("Total_Profit", ascending=False)
    pareto["Cumulative Profit %"] = pareto["Total_Profit"].cumsum() / pareto["Total_Profit"].sum()*100
    pareto_rev = product_perf.sort_values("Total_Sales", ascending=False)
    pareto_rev["Cumulative Revenue %"] = pareto_rev["Total_Sales"].cumsum() / pareto_rev["Total_Sales"].sum()*100

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=pareto["Cumulative Profit %"], mode='lines+markers', name="Cumulative Profit %", line=dict(color="#2ca02c")))
    fig.add_trace(go.Scatter(y=pareto_rev["Cumulative Revenue %"], mode='lines+markers', name="Cumulative Revenue %", line=dict(color="#1f77b4")))
    fig.add_hline(y=80, line_dash="dash", line_color="red")
    fig.update_layout(yaxis_title="Cumulative %", xaxis_title="Products Sorted by Profit/Revenue", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# STRATEGIC RECOMMENDATIONS
# ---------------------------
def recommendation_page():
    st.title("Strategic Recommendations")
    low_margin = product_perf[product_perf["Avg_Margin"] < 15]
    concentration = product_perf.sort_values("Total_Profit", ascending=False).head(10)["Total_Profit"].sum()/product_perf["Total_Profit"].sum()*100

    st.markdown(f"""
    **Key Strategic Insights:**
    - {len(low_margin)} products operate below 15% margin and require pricing review.
    - Top 10 products contribute {concentration:.1f}% of total profit, indicating concentration risk.
    - Strategic Core products should be protected and prioritized.
    - Volume Illusion products require margin improvement strategies.
    """)
    if not low_margin.empty:
        st.subheader("Low-Margin Products (<15%)")
        st.dataframe(low_margin[["Product Name","Division","Factory","Avg_Margin","Total_Profit","Strategic Category"]])

# ---------------------------
# PAGE ROUTING
# ---------------------------
if page == "Executive Intelligence":
    executive_page()
elif page == "Product Portfolio Analysis":
    product_portfolio_analysis()
elif page == "Division & Factory Performance":
    division_factory_page()
elif page == "Cost & Margin Diagnostics":
    cost_margin_page()
elif page == "Profit Concentration Analysis":
    pareto_page()
elif page == "Strategic Recommendations":
    recommendation_page()
