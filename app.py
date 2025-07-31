# Import tab modules
from tabs import overall, region, creative, audience, test_overall, test_overall_enhanced
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import json
from streamlit_extras.stylable_container import stylable_container
import time
from components import kpi_card

# Configure page settings for better performance
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="Campaign Dashboard",
    page_icon="📊"
)

# Load CSS with caching to avoid reloading
@st.cache_data
def load_css():
    with open("app/style.css") as css:
        return css.read()

st.markdown(f'<style>{load_css()}</style>', unsafe_allow_html=True)

# Initialize session state for better UX
def init_session_state():
    """Initialize session state variables for better performance"""
    if "previous_selection" not in st.session_state:
        st.session_state.previous_selection = "Overall"
    if "filters_cache" not in st.session_state:
        st.session_state.filters_cache = {}
    if "data_cache" not in st.session_state:
        st.session_state.data_cache = {}

init_session_state()

# Load secrets
host = st.secrets["mysql"]["host"]
database = st.secrets["mysql"]["database"]
user = st.secrets["mysql"]["user"]
password = st.secrets["mysql"]["password"]

# Connect to database
try:
    connection = mysql.connector.connect(
        host=host,
        database=database,
        user=user,
        password=password)
    cursor = connection.cursor()
except Error as e:
    st.error(f"Error connecting to MySQL: {e}")

# Enhanced query function with progress indicator
@st.cache_data
def query_data(
    columns: list,
    tablename: str,
    filters: dict,
    start_date=None,
    end_date=None,
    aggregations: dict = None,  # e.g., {"Impression": "SUM", "Cost": "AVG"}
    group_by: list = None       # e.g., ["Region", "Platform"]
):
    # Build SELECT clause
    if aggregations:
        select_parts = [
            f"{aggregations[col]}({col}) AS {col}" if col in aggregations else col
            for col in columns
        ]
    else:
        select_parts = columns

    column_str = ", ".join(select_parts)

    # Build WHERE clause
    where_clauses = []
    values = []

    for col, value in filters.items():
        where_clauses.append(f"{col} = %s")
        values.append(value)

    if start_date:
        where_clauses.append("report_date >= %s")
        values.append(start_date)

    if end_date:
        where_clauses.append("report_date <= %s")
        values.append(end_date)

    where_clause = " AND ".join(where_clauses)

    # Construct query
    query = f"SELECT {column_str} FROM {tablename}"
    if where_clause:
        query += f" WHERE {where_clause}"
    if aggregations and group_by:
        query += " GROUP BY " + ", ".join(group_by)

    # Execute query
    cursor.execute(query, values)
    data = cursor.fetchall()

    # Determine result columns for DataFrame
    if aggregations:
        result_columns = group_by + [col for col in columns if col in aggregations]
    else:
        result_columns = columns

    return pd.DataFrame(data, columns=result_columns)


TABLE_NAME = "report_campaign_creative"

# === Helpers ===
def build_where_clause(filters, start_date=None, end_date=None):
    where_clauses = []
    values = []

    for col, val in filters.items():
        # REMOVED quotes around "col"
        where_clauses.append(f'{col} = %s')
        values.append(val)

    if start_date:
        where_clauses.append("report_date >= %s")
        values.append(start_date)
    if end_date:
        where_clauses.append("report_date <= %s")
        values.append(end_date)

    clause = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    return clause, values


@st.cache_data
def get_filtered_list(column, tablename, filters=None, start_date=None, end_date=None):
    filters = filters or {}
    where_clause, values = build_where_clause(filters, start_date, end_date)

    # Use TRIM() to clean the data being selected. Order by the column number.
    query = f'SELECT DISTINCT ({column}) FROM {tablename}{where_clause} ORDER BY 1'
    
    cursor.execute(query, tuple(values))
    # Filter out potential None or empty string results from TRIM
    return [row[0] for row in cursor.fetchall() if row[0]]


@st.cache_data
def get_filtered_date_range(tablename, filters=None):
    filters = filters or {}
    where_clause, values = build_where_clause(filters)

    query = f"SELECT MIN(report_date), MAX(report_date) FROM {tablename}{where_clause}"
    cursor.execute(query, tuple(values))
    return cursor.fetchone()


def get_date_input(min_date, max_date):
    if hasattr(min_date, 'date'):
        min_date = min_date.date()
    if hasattr(max_date, 'date'):
        max_date = max_date.date()

    date_range = st.date_input(
        "Select Report Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start, end = date_range
        if start > end:
            st.error("Start date must be on or before end date.")
            st.stop()
        return start, end
    else:
        st.warning("Please select a valid date range.")
        st.stop()
        
        
# === Sidebar UI ===
with st.sidebar:
    selected = option_menu(
        menu_title="dentsu",
        options=["Overall", "Audience", "Region", "Creative", "Test Overall", "Test Overall Enhanced"],
        icons=["house", "person", "geo-alt", "card-heading", "clipboard-data"],
        default_index=0,
        orientation="vertical",
    )
    
    st.header("Filters")
    active_filters = {}



    # Step 1: Brand
    brand_list = get_filtered_list("Brand", TABLE_NAME)
    selected_brand = st.selectbox("Select Brand", ["All"] + brand_list)
    if selected_brand != "All":
        active_filters["Brand"] = selected_brand

    # Step 2: Campaign Code
    campaign_list = get_filtered_list("Campaign_code", TABLE_NAME, filters=active_filters)
    selected_campaign = st.selectbox("Select Campaign Code", campaign_list)
    active_filters["Campaign_code"] = selected_campaign

    # Step 3: Date Range
    min_date, max_date = get_filtered_date_range(TABLE_NAME, filters=active_filters)
    if not min_date or not max_date:
        st.warning("No data found for the current Brand/Campaign selection.")
        st.stop()
    start_date, end_date = get_date_input(min_date, max_date)    
    start_date, end_date = min_date, max_date

    # Step 4: Platform
    platform_list = get_filtered_list(
        "Platform", TABLE_NAME, filters=active_filters, start_date=start_date, end_date=end_date
    )
    selected_platform = st.selectbox("Select Platform", ["All"] + platform_list)
    if selected_platform != "All":
        active_filters["Platform"] = selected_platform
from st_aggrid import JsCode, AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode    

# Enhanced tab switching with a real-time loading animation
def display_tab_with_loading(tab_name, display_func, *args):
    """Displays a real-time CSS loading animation while data is being fetched."""
    
    loading_html = f"""
    <style>
    .loader {{
      border: 5px solid #f3f3f3; /* Light grey */
      border-top: 5px solid #3498db; /* Blue */
      border-radius: 50%;
      width: 50px;
      height: 50px;
      animation: spin 1s linear infinite;
      margin: 20px auto;
    }}
    @keyframes spin {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}
    </style>
    <div style="text-align: center; padding: 3rem;">
        <div class="loader"></div>
        <h2 style="color: #2E86AB; margin-bottom: 1rem;">Loading {tab_name}...</h2>
        <p style="color: #666; font-size: 1.1rem;">Preparing your dashboard, please wait.</p>
    </div>
    """
    
    # Placeholder for the loading animation
    loading_placeholder = st.empty()
    
    try:
        # Display the CSS-based loading animation
        loading_placeholder.markdown(loading_html, unsafe_allow_html=True)
        
        # Call the function to load data and display content.
        # The CSS animation will continue to spin in the browser
        # while this function blocks and fetches data.
        display_func(*args)
        
        # Clear the loading animation once the content is loaded and displayed
        loading_placeholder.empty()
        
        # Update session state to prevent re-showing animation on simple interaction
        st.session_state.previous_selection = selected

    except Exception as e:
        # If an error occurs, clear the animation and show the error
        loading_placeholder.empty()
        st.error(f"Error loading {tab_name}: {str(e)}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

# Display the selected tab with enhanced loading
if selected == "Overall":
    display_tab_with_loading("Overall", overall.display, query_data, active_filters, start_date, end_date)
elif selected == "Region":
    display_tab_with_loading("Region", region.display, query_data, active_filters, start_date, end_date)
elif selected == "Creative":
    display_tab_with_loading("Creative", creative.display, query_data, active_filters, start_date, end_date)
elif selected == "Audience":
    display_tab_with_loading("Audience", audience.display, query_data, active_filters, start_date, end_date, selected_platform)
elif selected == "Test Overall":
    display_tab_with_loading("Test Overall", test_overall.display, query_data, active_filters, start_date, end_date)
elif selected == "Test Overall Enhanced":
    display_tab_with_loading("Test Overall Enhanced", test_overall_enhanced.display, query_data, active_filters, start_date, end_date)