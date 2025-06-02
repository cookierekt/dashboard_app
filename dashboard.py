import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="US Economic Data Dashboard", layout="wide")
EXCEL_FILE = 'USA.xlsx'

# Sheet names and friendly titles
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

# --- Helper for parsing unemployment rate sheet
def parse_unemployment_sheet(file, sheet_name):
    df_raw = pd.read_excel(file, sheet_name=sheet_name, header=None)
    header_row = df_raw[df_raw.iloc[:, 0] == 'Year'].index
    if len(header_row) == 0:
        st.error("Unemployment sheet: Could not find 'Year' row.")
        st.stop()
    header_row = header_row[0]
    df = pd.read_excel(file, sheet_name=sheet_name, header=header_row)
    df = df.loc[:, ~df.columns.isna()]
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    keep_cols = ['Year'] + months
    df = df[keep_cols]
    df = df.dropna(subset=['Year'])
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    for m in months:
        df[m] = pd.to_numeric(df[m], errors='coerce')
    df['Yearly Avg'] = df[months].mean(axis=1)
    return df

st.title("🇺🇸 US Economic Data Dashboard")
st.markdown("> Interactive dashboard for tracking key US macroeconomic indicators.")

selected_sheet = st.sidebar.selectbox("Select Economic Indicator", list(sheet_dict.keys()), format_func=lambda x: sheet_dict[x])

# --- Unemployment Sheet Handling
if selected_sheet == 'Unemployment Rate':
    df = parse_unemployment_sheet(EXCEL_FILE, selected_sheet)
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    display_type = st.sidebar.radio("Show", ["Yearly Average", "Monthly"])
    if display_type == "Yearly Average":
        data = pd.DataFrame({
            'Year': df['Year'],
            'Value': df['Yearly Avg']
        }).dropna()
        chart_label = "Yearly Average"
    else:
        month = st.sidebar.selectbox("Month", months)
        data = pd.DataFrame({
            'Year': df['Year'],
            'Value': df[month]
        }).dropna()
        chart_label = f"Monthly ({month})"
    data['YoY Growth %'] = data['Value'].pct_change() * 100
    title_extra = f" - {chart_label}"

# --- All Other Sheets
else:
    # Try to auto-detect header row
    df = None
    header_found = False
    for skip in range(5, 12):
        try:
            temp_df = pd.read_excel(EXCEL_FILE, sheet_name=selected_sheet, skiprows=skip)
            columns = [str(col).strip() for col in temp_df.columns]
            if any(col.lower() in ["line", "description"] for col in columns):
                df = temp_df
                df.columns = columns
                header_found = True
                break
        except Exception as e:
            continue
    if not header_found or df is None:
        st.error("Could not detect the header or the required columns in the sheet.")
        st.stop()
    # Sub-indicator column search
    indicator_col = None
    for col in ["Description", "Line", "Indicator", "Unnamed: 0"]:
        if col in df.columns:
            indicator_col = col
            break
    year_cols = [col for col in df.columns if str(col).isdigit() and len(str(col)) == 4]
    if not year_cols:
        st.error("No year columns found! Data might be in an unexpected format.")
        st.stop()
    # Sub-indicator selection if available
    if indicator_col:
        indicator_options = df[indicator_col].dropna().unique()
        chosen_indicator = st.sidebar.selectbox(f"Select {indicator_col}", indicator_options)
        row = df[df[indicator_col] == chosen_indicator].iloc[0]
        title_extra = f" - {chosen_indicator}"
    else:
        row = df.iloc[0]
        title_extra = ""
    # Prepare for plotting
    data = pd.DataFrame({
        'Year': [int(yr) for yr in year_cols],
        'Value': row[year_cols].values
    }).dropna()
    data['YoY Growth %'] = data['Value'].pct_change() * 100

# --- Data preview
with st.expander("🔍 Preview Raw Data"):
    st.dataframe(df.head(12), use_container_width=True)

# --- Plot
chart_type = st.radio("Chart Type", ["Line", "Bar"], horizontal=True)
fig = px.line(data, x='Year', y='Value', title=f"{sheet_dict[selected_sheet]}{title_extra}", markers=True) if chart_type == "Line" \
    else px.bar(data, x='Year', y='Value', title=f"{sheet_dict[selected_sheet]}{title_extra}")
fig.update_layout(xaxis_title="Year", yaxis_title=sheet_dict[selected_sheet])
st.plotly_chart(fig, use_container_width=True)

# --- Metrics
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

# --- Professional Insight
st.markdown("### 📈 Professional Insight")
try:
    years_numeric = pd.to_numeric(data['Year'], errors='coerce')
    values_numeric = pd.to_numeric(data['Value'], errors='coerce')
    mask = (~years_numeric.isna()) & (~values_numeric.isna())
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

# --- Growth rates
if data['YoY Growth %'].notnull().sum() > 2:
    st.markdown("#### Year-on-Year Growth Rate")
    fig2 = px.bar(data, x='Year', y='YoY Growth %', title=f"Year-on-Year Growth Rate - {sheet_dict[selected_sheet]}{title_extra}")
    fig2.update_layout(yaxis_title="YoY Growth (%)")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Year-on-year growth rate not available for this indicator.")

st.caption("Data Source: US Bureau of Economic Analysis, Bureau of Labor Statistics, FRED, etc.")
