import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="US Economic Data Dashboard", layout="wide")
EXCEL_FILE = 'USA.xlsx'

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

line_name_map = {
    "1": "Personal income",
    "2": "Compensation of employees",
    "3": "Wages and salaries",
    "4": "Private industries",
    "5": "Government",
    "6": "Supplements to wages and salaries",
    "7": "Employer contributions for employee pension and insurance funds1",
    "8": "Employer contributions for government social insurance",
    "9": "Proprietors' income with inventory valuation and capital consumption adjustments",
    "10": "Farm",
    "11": "Nonfarm",
    "12": "Rental income of persons with capital consumption adjustment",
    "13": "Personal income receipts on assets",
    "14": "Personal interest income",
    "15": "Personal dividend income",
    "16": "Personal current transfer receipts",
    "17": "Government social benefits to persons",
    "18": "Social security2",
    "19": "Medicare3",
    "20": "Medicaid",
    "21": "Unemployment insurance",
    "22": "Veterans' benefits",
    "23": "Other",
    "24": "Other current transfer receipts, from business (net)",
    "25": "Less: Contributions for government social insurance, domestic"
}

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

st.title("US Economic Data Dashboard")
st.markdown("**Made by Rohan Singh**")
st.markdown("> Interactive dashboard for tracking key US macroeconomic indicators.")

selected_sheet = st.sidebar.selectbox("Select Economic Indicator", list(sheet_dict.keys()), format_func=lambda x: sheet_dict[x])
st.subheader(f"\U0001F4C2 {sheet_dict[selected_sheet]}")

if selected_sheet == 'Unemployment Rate':
    df = parse_unemployment_sheet(EXCEL_FILE, selected_sheet)
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    display_type = st.sidebar.radio("Show", ["Yearly Average", "Monthly"], horizontal=True)
    if display_type == "Yearly Average":
        data = pd.DataFrame({'Year': df['Year'], 'Value': df['Yearly Avg']}).dropna()
        chart_label = "Yearly Average"
    else:
        month = st.sidebar.selectbox("Month", months)
        data = pd.DataFrame({'Year': df['Year'], 'Value': df[month]}).dropna()
        chart_label = f"Monthly ({month})"
    data['YoY Growth %'] = data['Value'].pct_change() * 100
    title_extra = f" - {chart_label}"

else:
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
        except Exception:
            continue
    if not header_found or df is None:
        st.error("Could not detect the header or the required columns in the sheet.")
        st.stop()

    indicator_col = next((col for col in ["Description", "Line", "Indicator", "Unnamed: 0"] if col in df.columns), None)
    year_cols = [col for col in df.columns if str(col).isdigit() and len(str(col)) == 4]
    if not year_cols:
        st.error("No year columns found! Data might be in an unexpected format.")
        st.stop()

    if selected_sheet == 'Personal Income' and indicator_col == 'Line':
        indicator_options = df['Line Name'].dropna().unique()
        chosen_line_name = st.sidebar.selectbox("Select Line Item", indicator_options)
        line_number = [k for k, v in line_name_map.items() if v == chosen_line_name]
        row = df[df['Line'].astype(int).astype(str).isin(line_number)].iloc[0]
        title_extra = f" - {chosen_line_name}"
    elif indicator_col:
        indicator_options = df[indicator_col].dropna().unique()
        chosen_indicator = st.sidebar.selectbox(f"Select {indicator_col}", indicator_options)
        row = df[df[indicator_col] == chosen_indicator].iloc[0]
        title_extra = f" - {chosen_indicator}"
    else:
        row = df.iloc[0]
        title_extra = ""

    data = pd.DataFrame({
        'Year': [int(yr) for yr in year_cols],
        'Value': row[year_cols].values
    }).dropna()
    data['YoY Growth %'] = data['Value'].pct_change() * 100

min_year, max_year = int(data['Year'].min()), int(data['Year'].max())
year_range = st.slider("Select Year Range", min_year, max_year, (min_year, max_year), step=1)
data = data[(data['Year'] >= year_range[0]) & (data['Year'] <= year_range[1])]

with st.expander("\U0001F50D Preview Raw Data"):
    st.dataframe(df.head(12), use_container_width=True)

fig = px.line(data, x='Year', y='Value', title=f"{sheet_dict[selected_sheet]}{title_extra}", markers=True)
fig.update_layout(xaxis_title="Year", yaxis_title=sheet_dict[selected_sheet], title_x=0.5)
st.plotly_chart(fig, use_container_width=True)

st.subheader("\U0001F4CA Key Metrics & Analysis")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Latest Value", f"{data['Value'].iloc[-1]:,.2f}")
with col2:
    yoy = data['YoY Growth %'].iloc[-1]
    st.metric("Latest YoY Growth (%)", f"{yoy:.2f}%" if pd.notnull(yoy) else "N/A")
with col3:
    avg = data['Value'].mean()
    st.metric("Average (All Years)", f"{avg:,.2f}")

st.markdown("### \U0001F4C8 Professional Insight")
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

if data['YoY Growth %'].notnull().sum() > 2:
    st.markdown("#### Year-on-Year Growth Rate")
    fig2 = px.bar(data, x='Year', y='YoY Growth %', title=f"Year-on-Year Growth Rate - {sheet_dict[selected_sheet]}{title_extra}")
    fig2.update_layout(yaxis_title="YoY Growth (%)", title_x=0.5)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Year-on-year growth rate not available for this indicator.")

st.caption("Data Source: US Bureau of Economic Analysis, Bureau of Labor Statistics, FRED, etc.")
