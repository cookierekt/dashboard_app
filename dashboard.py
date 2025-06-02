import streamlit as st
import pandas as pd
import plotly.express as px
import os
import webbrowser

# Open the browser automatically (only on first run)
def auto_open_browser():
    if not os.environ.get("_STREAMLIT_BROWSER_OPENED"):
        webbrowser.open_new("http://localhost:8501")
        os.environ["_STREAMLIT_BROWSER_OPENED"] = "1"

st.set_page_config(page_title="US Economic Data Dashboard", layout="wide")
auto_open_browser()

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
st.write(
    "Interactive dashboard of US economic indicators. "
    "Select a data type on the left sidebar to view its chart."
)

selected_sheet = st.sidebar.selectbox(
    "Select Economic Indicator",
    sheet_names
)

# Try loading the sheet, handling possible format quirks
try:
    df = pd.read_excel(EXCEL_FILE, sheet_name=selected_sheet, skiprows=5)
    indicator_name = df.iloc[0, 0]
    years = df.columns[1:]
    values = df.iloc[0, 1:].values

    data = pd.DataFrame({
        'Year': years,
        'Value': values
    })
    data['Year'] = data['Year'].astype(str)
    data = data.dropna()

    fig = px.line(
        data,
        x='Year',
        y='Value',
        title=f"{indicator_name} Over Time",
        markers=True,
    )
    fig.update_layout(xaxis_title="Year", yaxis_title=indicator_name)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Could not load data for {selected_sheet}. Error: {e}")
    st.write("Please check your Excel file's formatting.")

st.markdown("---")
st.caption("Created by [Your Name]. Powered by Streamlit & Plotly.")
