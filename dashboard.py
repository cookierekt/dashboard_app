import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="US Economic Data Dashboard", layout="wide")
EXCEL_FILE = 'USA.xlsx'

sheet_names = [
    'Nominal GDP',
    'Real GDP',
    'Real GDP Perc Change',
    'Contribution to real GDP',
    'Personal Income',
    'PCE',
    'Govt receipts and exp',
    'Saving and Investing by sector',
    'Unemployment Rate'
]

st.title("🇺🇸 US Economic Data Dashboard")
st.write("Interactive dashboard of US economic indicators. Select a data type on the left sidebar to view its chart.")

selected_sheet = st.sidebar.selectbox("Select Economic Indicator", sheet_names)

# Try reading the sheet with multiple possible skiprows
# Find the first row that contains "Line" or "Description" and treat it as the header
for skip in range(5, 10):  # Try different rows for header
    df = pd.read_excel(EXCEL_FILE, sheet_name=selected_sheet, skiprows=skip)
    if "Line" in df.columns or "Description" in df.columns:
        break

st.write("Raw data preview:")
st.write(df.head(10))

# Find the first non-empty indicator row (skip NaN)
row_idx = df[df['Line'].notna()].index[0]
row = df.loc[row_idx]
years = df.columns[df.columns.str.match(r"^\d{4}$")]
values = row[years].values

data = pd.DataFrame({
    'Year': years,
    'Value': values
})

data = data.dropna()

fig = px.line(data, x='Year', y='Value', title=f"{selected_sheet} Over Time", markers=True)
fig.update_layout(xaxis_title="Year", yaxis_title=selected_sheet)
st.plotly_chart(fig, use_container_width=True)
