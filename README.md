# 🛍️ Customer Shopping Behavior Analytics Dashboard

A powerful, interactive **Streamlit dashboard** for analyzing customer shopping behavior. Built with **Python**, **pandas**, **Plotly**, **DuckDB**, and integrated with **Google Gemini AI** for natural language SQL querying and business insights.

> Transform raw retail transaction data into actionable business intelligence through interactive dashboards and AI-powered analytics.

---

# ✨ Features

## 📊 Core Analytics (8 Dedicated Tabs)

### 💰 Revenue Analytics
- Revenue by Gender
- Revenue by Age Group
- Revenue by Product Category
- Seasonal Revenue Trends
- Subscription vs Non-Subscription Revenue
- Discount & Promo Impact
- Interactive KPIs

### 👥 Customer Analytics
- Customer Segmentation
  - New
  - Returning
  - Loyal
- Customer Lifetime Value (CLV Proxy)
- Age Group Analysis
- Subscription Analysis
- Customer Cohort Heatmaps

### 🛒 Product Analytics
- Top & Bottom Performing Products
- Product Ratings Analysis
- Size & Color Popularity
- Category Performance
- Product Affinity
  - "Customers who bought X also bought Y"

### 🎯 Discount & Promotion Analytics
- Discount Effectiveness
- Promo Code Performance
- Average Order Value Impact
- Category-wise Discount Usage
- Rating Differences (Discount vs No Discount)

### 🚚 Shipping Analytics
- Shipping Method Performance
- Category-wise Shipping Preferences
- High-value Customer Shipping Habits
- Shipping Revenue Analysis

### 🌍 Geographic Analytics
- Top Revenue States
- Average Order Value by State
- Customer Ratings by State
- Subscription Rate
- Discount Usage by Location

### 💳 Payment Analytics
- Revenue by Payment Method
- Payment Preferences
- Average Order Value
- Discount Sensitivity
- Age-wise Payment Trends

### 📈 Advanced Analytics
- Correlation Matrix
- CLV by Customer Segment
- Seasonal Trends
- Revenue Lift Opportunities
- High-value Customer (Top 10%) Analysis

---

# 🤖 AI SQL Assistant

Ask business questions in plain English.

### Examples

```text
Show revenue by category for female customers in California

Top 10 products by revenue

Average purchase amount by age group

Which shipping method generates the highest revenue?

Show subscription customers with highest CLV
```

The assistant automatically:

- Converts English → DuckDB SQL
- Executes the SQL query
- Displays interactive tables
- Creates Plotly visualizations
- Generates concise business insights using Gemini AI

---

# 🎛️ Interactive Filters

The sidebar contains dynamic filters for:

- Gender
- Age Group
- Product Category
- Season
- Subscription Status
- Discount Applied
- Promo Code Used
- Shipping Type
- Location

### Additional Controls

- Reset Filters (One Click)
- Real-time Dashboard Updates
- Dynamic KPIs

---

# 📊 Key Metrics

- Total Revenue
- Total Transactions
- Average Order Value (AOV)
- Unique Customers
- Average CLV Proxy
- Customer Segments
- Cohort Analysis
- Product Affinity
- Revenue Lift Estimation

---

# 📁 Project Structure

```text
customer_shopping_behavior/
│
├── app.py
├── data_loader.py
├── ai_assistant.py
├── config.py
├── requirements.txt
├── customer_shopping_behavior_cleaned.csv
├── customer_shopping_behavior.csv
├── Data Cleaning & SQL.ipynb
├── Executive Report.pdf
│
├── tabs/
│   ├── __init__.py
│   ├── revenue.py
│   ├── customer.py
│   ├── product.py
│   ├── discount_promo.py
│   ├── shipping.py
│   ├── geographic.py
│   ├── payment.py
│   ├── advanced.py
│   └── ai_sql.py
│
└── supporting_docs/
    ├── Data Dictionary.pdf
    └── Test Questions for Assistant.pdf
```

---

# 🚀 Quick Start

## 1. Clone the Repository

```bash
git clone https://github.com/adityadev343/customer_shopping_behavior.git
cd customer_shopping_behavior
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure Gemini API (Optional)

Create:

```text
.streamlit/secrets.toml
```

```toml
GEMINI_API_KEY_1="your_key_here"
GEMINI_API_KEY_2="optional_key"
# Add up to GEMINI_API_KEY_5
```

> The dashboard works without Gemini, but the AI SQL Assistant requires valid API keys.

## 4. Run the Application

```bash
streamlit run app.py
```

---

# 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Data Processing | pandas, NumPy |
| SQL Engine | DuckDB |
| Visualization | Plotly |
| AI | Google Gemini (gemini-2.5-flash) |
| Caching | Streamlit Cache |

---

# 🎯 Use Cases

### Retail Analysts
- Discover high-performing products
- Analyze customer segments
- Monitor revenue trends

### Marketing Teams
- Optimize discounts
- Improve campaign targeting
- Increase customer retention

### Operations Teams
- Improve shipping strategy
- Optimize logistics
- Identify regional opportunities

### Executives
- Executive dashboards
- Revenue monitoring
- Business insights

### Data Enthusiasts
- Natural language SQL
- Interactive analytics
- AI-powered exploration

---

# ⭐ Future Enhancements

- Forecasting Models
- Recommendation System
- Customer Churn Prediction
- Inventory Analytics
- Export to Excel/PDF
- Scheduled Reports

