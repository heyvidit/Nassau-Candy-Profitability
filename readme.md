# Nassau Candy Distributor – Product Line Profitability & Margin Performance Analysis

## 📌 Project Overview
This project delivers a **profit-focused analytical framework** for Nassau Candy Distributor. Instead of relying on sales volume alone, the analysis identifies which product lines and divisions truly **drive profitability**, which products pose **margin risk**, and where **pricing, sourcing, or portfolio rationalization** is required.

The solution combines **Python-based analytics** with an **interactive Streamlit dashboard** designed for executive and stakeholder decision-making.

---

## 🎯 Business Objectives
- Identify products with **high profit and strong margins**
- Detect **high-sales but low-margin** products that weaken overall performance
- Compare **division-level efficiency** (revenue vs profit imbalance)
- Measure **profit concentration risk** using Pareto analysis
- Support data-driven decisions on pricing, cost control, and product strategy

---

## 🗂 Dataset Description
The dataset contains **10,194 transaction-level records** with the following key attributes:
- Sales, Cost, Gross Profit, Units
- Product hierarchy (Product, Division)
- Time (Order Date, Ship Date)
- Geography (Region, State, City)

Each row represents a **product-level order line**, enabling granular profitability analysis.

---

## 📊 Key Metrics
- **Gross Margin (%)** = Gross Profit ÷ Sales
- **Profit per Unit** = Gross Profit ÷ Units
- **Revenue Contribution**
- **Profit Contribution**

---

## 🖥 Streamlit Dashboard Features
### Modules
- Product Profitability Leaderboard
- Division Revenue vs Profit Comparison
- Cost vs Margin Diagnostics
- Profit Concentration (Pareto Analysis)

### User Controls
- Date range selector
- Division filter
- Margin threshold slider
- Product search

---

## 📁 Repository Structure
```
Nassau-Candy-Profitability/
│
├── app.py
├── Nassau Candy Distributor (1).csv
├── requirements.txt
├── README.md
```

---

## ⚙️ How to Run the App
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🧠 Business Value
This project shifts decision-making from **revenue-driven intuition** to **profit-driven strategy**, enabling Nassau Candy Distributor to:
- Protect high-margin products
- Fix or eliminate margin drainers
- Improve long-term financial efficiency

---

## 📌 Author
Senior Data Analytics Project – Product Profitability & Margin Optimization

