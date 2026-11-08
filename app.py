import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import zipfile
import io

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Retail Business Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CUSTOM CSS
# ==========================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.block-container {
    padding-top: 2rem;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.04);
}

[data-testid="stMetricLabel"] {
    color: #64748b;
}

[data-testid="stMetricValue"] {
    color: #17365d;
    font-weight: bold;
}

h1 {
    color: #17365d;
}

h2, h3 {
    color: #23476b;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. HEADER
# ==========================================

st.title("📊 Retail Business Performance Dashboard")

st.markdown(
    "Interactive Business Intelligence | Sales Analytics | Customer Insights"
)

st.caption(
    "Analyze retail performance through interactive KPIs, "
    "sales trends and customer behaviour."
)

st.divider()


# ==========================================
# 4. DATASET UPLOAD
# ==========================================

st.sidebar.title("📁 Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload Online Retail II Dataset",
    type=["xlsx", "zip"]
)


@st.cache_data(show_spinner="Loading and processing dataset...")
def load_data(file_bytes, file_type):

    if file_type == "zip":

        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:

            excel_files = [
                name for name in archive.namelist()
                if name.lower().endswith(".xlsx")
                and not name.startswith("__MACOSX/")
            ]

            if not excel_files:
                raise ValueError(
                    "No Excel workbook found inside the ZIP file."
                )

            # Locate the Online Retail II workbook
            selected_file = next(
                (
                    name for name in excel_files
                    if "online_retail_ii" in name.lower()
                ),
                excel_files[0]
            )

            excel_bytes = archive.read(selected_file)

    else:
        excel_bytes = file_bytes

    sheets = pd.read_excel(
        io.BytesIO(excel_bytes),
        sheet_name=None
    )

    data = pd.concat(
        sheets.values(),
        ignore_index=True
    )

    # Standardize column names
    data.columns = data.columns.str.strip()

    required_columns = [
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Correct data types
    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"],
        errors="coerce"
    )

    data["Quantity"] = pd.to_numeric(
        data["Quantity"],
        errors="coerce"
    )

    data["Price"] = pd.to_numeric(
        data["Price"],
        errors="coerce"
    )

    data["Customer ID"] = data["Customer ID"].astype("string")

    # Remove duplicates
    data = data.drop_duplicates()

    # Keep valid completed sales
    data = data[
        (data["Quantity"] > 0) &
        (data["Price"] > 0) &
        (data["InvoiceDate"].notna()) &
        (~data["Invoice"].astype(str).str.startswith("C"))
    ].copy()

    # Calculate revenue
    data["Revenue"] = (
        data["Quantity"] * data["Price"]
    )

    # Date features
    data["Year"] = data["InvoiceDate"].dt.year

    data["Month"] = data["InvoiceDate"].dt.month

    data["Year_Month"] = (
        data["InvoiceDate"].dt.to_period("M").astype(str)
    )

    return data


if uploaded_file is None:

    st.info(
        "Please upload your Online Retail II ZIP or Excel dataset "
        "using the button in the left sidebar."
    )

    st.stop()


try:

    df = load_data(
        uploaded_file.getvalue(),
        uploaded_file.name.split(".")[-1].lower()
    )

except Exception as error:

    st.error(f"Dataset loading failed: {error}")
    st.stop()


st.sidebar.success("Dataset loaded successfully!")

st.sidebar.write(
    f"Total records: {len(df):,}"
)


# ==========================================
# 5. SIDEBAR FILTERS
# ==========================================

st.sidebar.divider()

st.sidebar.header("🔍 Dashboard Filters")

# Country filter
country_options = sorted(
    df["Country"].dropna().unique().tolist()
)

selected_countries = st.sidebar.multiselect(
    "Select Countries",
    country_options,
    default=[]
)

# Year filter
year_options = sorted(
    df["Year"].dropna().unique().tolist()
)

selected_years = st.sidebar.multiselect(
    "Select Years",
    year_options,
    default=year_options
)

# Product filter
product_options = sorted(
    df["Description"].dropna().unique().tolist()
)

selected_products = st.sidebar.multiselect(
    "Select Products",
    product_options,
    default=[],
    max_selections=20
)


# ==========================================
# 6. APPLY FILTERS
# ==========================================

filtered = df[
    df["Year"].isin(selected_years)
].copy()

if selected_countries:

    filtered = filtered[
        filtered["Country"].isin(selected_countries)
    ]

if selected_products:

    filtered = filtered[
        filtered["Description"].isin(selected_products)
    ]


if filtered.empty:

    st.warning(
        "No records found for the selected filters. "
        "Please change your selections."
    )

    st.stop()


# ==========================================
# 7. EXECUTIVE KPI CALCULATIONS
# ==========================================

total_revenue = filtered["Revenue"].sum()

total_orders = filtered["Invoice"].nunique()

total_customers = filtered["Customer ID"].nunique()

average_order_value = (
    total_revenue / total_orders
    if total_orders > 0 else 0
)

# First observed customers in the selected period
customer_first_purchase = (
    filtered.dropna(subset=["Customer ID"])
    .groupby("Customer ID")["InvoiceDate"]
    .min()
)

first_observed_customers = (
    customer_first_purchase.dt.year.nunique()
    if False else len(customer_first_purchase)
)

# ==========================================
# 8. KPI CARDS
# ==========================================

st.subheader("Executive KPI Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"£{total_revenue:,.2f}"
)

col2.metric(
    "Average Order Value",
    f"£{average_order_value:,.2f}"
)

col3.metric(
    "Total Customers",
    f"{total_customers:,}"
)

col4.metric(
    "Total Orders",
    f"{total_orders:,}"
)

col5, col6 = st.columns(2)

col5.metric(
    "First-Observed Customers",
    f"{first_observed_customers:,}"
)

col6.metric(
    "Customer Acquisition Cost",
    "N/A"
)

st.caption(
    "CAC and churn rate are unavailable because the dataset "
    "does not contain marketing expenditure or sufficient "
    "customer subscription/churn information. "
    "First-observed customers are not necessarily new acquisitions."
)


# ==========================================
# 9. MONTHLY REVENUE TREND
# ==========================================

st.divider()

st.subheader("📈 Monthly Revenue Performance")

monthly_sales = (
    filtered.groupby("Year_Month")["Revenue"]
    .sum()
    .reset_index()
)

fig_monthly = px.area(
    monthly_sales,
    x="Year_Month",
    y="Revenue",
    markers=True,
    title="Monthly Revenue Trend",
    color_discrete_sequence=["#2563eb"]
)

fig_monthly.update_layout(
    template="plotly_white",
    xaxis_title="Month",
    yaxis_title="Revenue (£)",
    hovermode="x unified"
)

st.plotly_chart(
    fig_monthly,
    use_container_width=True
)


# ==========================================
# 10. GEOGRAPHIC SALES ANALYSIS
# ==========================================

st.divider()

st.subheader("🌍 Geographic Sales Distribution")

country_sales = (
    filtered.groupby("Country")["Revenue"]
    .sum()
    .reset_index()
)

fig_map = px.choropleth(
    country_sales,
    locations="Country",
    locationmode="country names",
    color="Revenue",
    hover_name="Country",
    color_continuous_scale="Blues",
    title="Revenue Distribution by Country"
)

fig_map.update_layout(
    template="plotly_white"
)

st.plotly_chart(
    fig_map,
    use_container_width=True
)


# ==========================================
# 11. TOP 10 COUNTRIES
# ==========================================

st.subheader("🏆 Top 10 Countries by Revenue")

top_countries = (
    country_sales.sort_values(
        "Revenue",
        ascending=False
    ).head(10)
)

fig_country = px.bar(
    top_countries,
    x="Revenue",
    y="Country",
    orientation="h",
    color="Revenue",
    color_continuous_scale="Blues",
    title="Highest Revenue Generating Countries"
)

fig_country.update_layout(
    template="plotly_white",
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(
    fig_country,
    use_container_width=True
)


# ==========================================
# 12. PRODUCT PERFORMANCE
# ==========================================

st.divider()

st.subheader("🛍️ Product Performance")

top_products = (
    filtered.groupby("Description")["Revenue"]
    .sum()
    .nlargest(10)
    .reset_index()
)

fig_products = px.bar(
    top_products,
    x="Revenue",
    y="Description",
    orientation="h",
    color="Revenue",
    color_continuous_scale="Teal",
    title="Top 10 Revenue Generating Products"
)

fig_products.update_layout(
    template="plotly_white",
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(
    fig_products,
    use_container_width=True
)


# ==========================================
# 13. CUSTOMER ANALYSIS
# ==========================================

st.divider()

st.subheader("👥 Customer Purchasing Behaviour")

customer_analysis = (
    filtered.dropna(subset=["Customer ID"])
    .groupby("Customer ID")
    .agg(
        Total_Orders=("Invoice", "nunique"),
        Total_Revenue=("Revenue", "sum")
    )
    .reset_index()
)

fig_customer = px.scatter(
    customer_analysis,
    x="Total_Orders",
    y="Total_Revenue",
    color="Total_Revenue",
    hover_data=["Customer ID"],
    color_continuous_scale="Viridis",
    title="Customer Order Frequency vs Revenue"
)

fig_customer.update_layout(
    template="plotly_white",
    xaxis_title="Number of Orders",
    yaxis_title="Total Revenue (£)"
)

st.plotly_chart(
    fig_customer,
    use_container_width=True
)


# ==========================================
# 14. YEAR AND MONTH DRILL-DOWN
# ==========================================

st.divider()

st.subheader("🔎 Sales Drill-Down Analysis")

drill_col1, drill_col2 = st.columns(2)

with drill_col1:

    drill_year = st.selectbox(
        "Choose Year",
        sorted(filtered["Year"].unique())
    )

with drill_col2:

    drill_month = st.selectbox(
        "Choose Month",
        ["All"] + list(range(1, 13))
    )

drill_data = filtered[
    filtered["Year"] == drill_year
].copy()

if drill_month != "All":

    drill_data = drill_data[
        drill_data["Month"] == drill_month
    ]

drill_summary = (
    drill_data.groupby("Country")
    .agg(
        Total_Revenue=("Revenue", "sum"),
        Total_Orders=("Invoice", "nunique")
    )
    .sort_values("Total_Revenue", ascending=False)
    .reset_index()
)

st.dataframe(
    drill_summary,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 15. DASHBOARD SUMMARY
# ==========================================

st.divider()

st.subheader("📋 Business Performance Summary")

best_country = country_sales.loc[
    country_sales["Revenue"].idxmax()
]

best_product = top_products.loc[
    top_products["Revenue"].idxmax()
]

st.markdown(f"""
- **Total Revenue:** £{total_revenue:,.2f}
- **Total Orders:** {total_orders:,}
- **Total Customers:** {total_customers:,}
- **Average Order Value:** £{average_order_value:,.2f}
- **Top Revenue Country:** {best_country['Country']}
- **Top Revenue Product:** {best_product['Description']}
""")


# ==========================================
# 16. DOWNLOAD FILTERED DATA
# ==========================================

st.divider()

st.subheader("📥 Export Dashboard Data")

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Dataset",
    data=csv_data,
    file_name="retail_dashboard_data.csv",
    mime="text/csv"
)


# ==========================================
# 17. FOOTER
# ==========================================

st.divider()

st.caption(
    "Retail Business Performance Dashboard | "
    "Developed using Python, Streamlit, Pandas and Plotly"
)

st.success(
    "Dashboard analysis completed successfully."
)

