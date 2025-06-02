import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="US Economic Data Dashboard", layout="wide")
EXCEL_FILE = 'USA.xlsx'

# Define sheet names and friendly titles
sheet_dict = {
    'Nominal GDP': "Nominal GDP (in billions USD)",
    'Real GDP': "Real GDP (chained, billions USD)",
    'Real GDP Perc Change': "Real GDP Percent Change",
    'Contribution to real GDP': "Contribution to Real GDP Growth",
    'Personal Income': "Personal Income (billions USD)",
    'PCE': "Personal Consumption Expenditures",
    'Govt receipts and exp': "Government Receipts & Expenditures",
    'Saving and Investing by sector': "Savings & Investments by Sector",
    'Unemployment Rate': "Unemployment Rate (%)"
}

st.title("🇺🇸 US Economic Data Dashboard")
st.markdown("> Interactive dashboard for tracking key US macroeconomic indicators.")

# Sidebar selector
selected_sheet = st.sidebar.selectbox("Select Economic Indicator", list(sheet_dict.keys()), format_func=lambda x: sheet_dict[x])

# Attempt to intelligently find the right header row
df = None
header_found = False
for skip in range(5, 11):
    try:
        temp_df = pd.read_excel(EXCEL_FILE, sheet_name=selected_sheet, skiprows=skip)
        columns = [str(col).strip() for col in temp_df.columns]
        if any(col.lower() in ["line", "description"] for col in columns):
            df = temp_df
            df.columns = columns  # Clean up columns
            header_found = True
            break
    except Exception as e:
        continue

if not header_found or df is None:
    st.error("Could not detect the header or the required columns in the sheet.")
    st.stop()

# Display raw data
with st.expander("🔍 Preview Raw Data"):
    st.dataframe(df.head(10), use_container_width=True)

# --- Intelligent column detection
indicator_col = None
for col in ["Description", "Line", "Indicator", "Unnamed: 0"]:
    if col in df.columns:
        indicator_col = col
        break

# Find year columns (numeric column headers, often 4-digit)
year_cols = [col for col in df.columns if str(col).isdigit() and len(str(col)) == 4]
if not year_cols:
    st.error("No year columns found! Data might be in an unexpected format.")
    st.stop()

# User selects a specific sub-indicator if available
if indicator_col:
    # Only show non-null indicator descriptions
    indicator_options = df[indicator_col].dropna().unique()
    chosen_indicator = st.sidebar.selectbox(f"Select {indicator_col}", indicator_options)
    row = df[df[indicator_col] == chosen_indicator].iloc[0]
    title_extra = f" - {chosen_indicator}"
else:
    # Fallback: use the first row
    row = df.iloc[0]
    title_extra = ""

# Prepare data for plotting
data = pd.DataFrame({
    'Year': [int(yr) for yr in year_cols],
    'Value': row[year_cols].values
}).dropna()

# Calculate growth rates if there are at least 2 years
data['YoY Growth %'] = data['Value'].pct_change() * 100

# Plot interactive line chart
fig = px.line(data, x='Year', y='Value', title=f"{sheet_dict[selected_sheet]}{title_extra} (Line Chart)", markers=True)
fig.update_layout(xaxis_title="Year", yaxis_title=sheet_dict[selected_sheet])

# Add option for users to switch to bar chart
chart_type = st.radio("Chart Type", ["Line", "Bar"], horizontal=True)
if chart_type == "Bar":
    fig = px.bar(data, x='Year', y='Value', title=f"{sheet_dict[selected_sheet]}{title_extra} (Bar Chart)")

st.plotly_chart(fig, use_container_width=True)

# Display summary statistics and analysis
st.subheader("📊 Key Metrics & Analysis")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Latest Value", f"{data['Value'].iloc[-1]:,.2f}")
with col2:
    yoy = data['YoY Growth %'].iloc[-1]
    st.metric("Latest YoY Growth (%)", f"{yoy:.2f}%" if pd.notnull(yoy) else "N/A")
with col3:
    avg = data['Value'].mean()
    st.metric("Average (All Years)", f"{avg:,.2f}")

# Professional analysis (dynamic comments)
st.markdown("### 📈 Professional Insight")
try:
    # Ensure numeric types for regression
    years_numeric = pd.to_numeric(data['Year'], errors='coerce')
    values_numeric = pd.to_numeric(data['Value'], errors='coerce')
    mask = (~years_numeric.isna()) & (~values_numeric.isna())
    # Only run if enough valid data
    if mask.sum() > 3:
        trend = np.polyfit(years_numeric[mask], values_numeric[mask], 1)[0]
        if trend > 0:
            trend_text = "an **upward trend**"
        elif trend < 0:
            trend_text = "a **downward trend**"
        else:
            trend_text = "a **stable pattern**"
        st.info(f"From {int(years_numeric[mask].min())} to {int(years_numeric[mask].max())}, this indicator shows {trend_text}. "
                f"Latest YoY change is **{yoy:.2f}%**. "
                f"Average value over the period: **{avg:,.2f}**.")
    else:
        st.warning("Not enough valid numeric data for trend analysis.")
except Exception as e:
    st.error(f"Trend analysis error: {e}")

# Show growth rates chart if relevant
if data['YoY Growth %'].notnull().sum() > 2:
    st.markdown("#### Year-on-Year Growth Rate")
    fig2 = px.bar(data, x='Year', y='YoY Growth %', title=f"Year-on-Year Growth Rate - {sheet_dict[selected_sheet]}{title_extra}")
    fig2.update_layout(yaxis_title="YoY Growth (%)")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Year-on-year growth rate not available for this indicator.")

st.caption("Data Source: US Bureau of Economic Analysis, Bureau of Labor Statistics, FRED, etc.")
