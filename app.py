# Import tab modules
from tabs import overall, region, creative, audience, test_overall, test_overall_enhanced, test_table
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

    # Handle date filtering - check if report_date exists, otherwise use Plan_Start_Date/Plan_End_Date
    if start_date or end_date:
        # First, check if report_date column exists in the table
        try:
            check_column_query = f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '{tablename}' AND column_name = 'report_date'"
            cursor.execute(check_column_query)
            has_report_date = cursor.fetchone()[0] > 0
            
            if has_report_date:
                # Use report_date if it exists
                if start_date:
                    where_clauses.append("report_date >= %s")
                    values.append(start_date)
                if end_date:
                    where_clauses.append("report_date <= %s")
                    values.append(end_date)
            else:
                # Fallback to Plan_Start_Date and Plan_End_Date if report_date doesn't exist
                if start_date:
                    where_clauses.append("Plan_Start_Date >= %s")
                    values.append(start_date)
                if end_date:
                    where_clauses.append("Plan_End_Date <= %s")
                    values.append(end_date)
        except Exception as e:
            # If we can't check the schema, skip date filtering to avoid errors
            st.warning(f"Could not determine date columns for {tablename}. Date filtering disabled.")
            pass

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
def build_where_clause(filters, start_date=None, end_date=None, tablename=None):
    where_clauses = []
    values = []

    for col, val in filters.items():
        # REMOVED quotes around "col"
        where_clauses.append(f'{col} = %s')
        values.append(val)

    # Handle date filtering - check if report_date exists, otherwise use Plan_Start_Date/Plan_End_Date
    if start_date or end_date:
        if tablename:
            # For now, skip date filtering to avoid schema checking issues
            # This will be handled by the main query_data function
            pass
        else:
            # Default to report_date if no table name provided (backward compatibility)
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
    where_clause, values = build_where_clause(filters, start_date, end_date, tablename)

    # Use TRIM() to clean the data being selected. Order by the column number.
    query = f'SELECT DISTINCT ({column}) FROM {tablename}{where_clause} ORDER BY 1'
    
    cursor.execute(query, tuple(values))
    # Filter out potential None or empty string results from TRIM
    return [row[0] for row in cursor.fetchall() if row[0]]


@st.cache_data
def get_filtered_date_range(tablename, filters=None):
    filters = filters or {}
    where_clause, values = build_where_clause(filters, None, None, tablename)

    # Check if report_date column exists, otherwise use Plan_Start_Date/Plan_End_Date
    try:
        check_column_query = f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '{tablename}' AND column_name = 'report_date'"
        cursor.execute(check_column_query)
        has_report_date = cursor.fetchone()[0] > 0
        
        if has_report_date:
            query = f"SELECT MIN(report_date), MAX(report_date) FROM {tablename}{where_clause}"
        else:
            query = f"SELECT MIN(Plan_Start_Date), MAX(Plan_End_Date) FROM {tablename}{where_clause}"
        
        cursor.execute(query, tuple(values))
        return cursor.fetchone()
    except Exception as e:
        # If we can't determine the schema, try with report_date as fallback
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
        # options=["Overall", "Audience", "Region", "Creative", "Test Overall", "Test Overall Enhanced", "Test Table"],
        options=["Overall", "Audience", "Region", "Creative", "Test Overall Enhanced", "Test Table"],

        icons=["house", "person", "geo-alt", "card-heading", "clipboard-data"],
        default_index=0,
        orientation="vertical",
    )
    
    st.header("Filters")
    active_filters = {}

    # --- Hierarchical Filters with DataFrame Filtering ---
    # Load data once and filter in memory for better performance
    
    # Load all filter data once at the beginning
    if 'filter_data' not in st.session_state:
        # Check what columns are available in the table
        try:
            # Try to get the data with report_date first
            filter_data = query_data(
                columns=["Brand", "Campaign_code", "Platform", "Funnel", "Format", "Region", "Audience", "Buying_Method", "report_date"],
                tablename=TABLE_NAME,
                filters={},
                start_date=None,
                end_date=None,
                aggregations={},
                group_by=[]
            )
        except Exception as e:
            # If report_date doesn't exist, try without it
            try:
                filter_data = query_data(
                    columns=["Brand", "Campaign_code", "Platform", "Funnel", "Format", "Region", "Audience", "Buying_Method"],
                    tablename=TABLE_NAME,
                    filters={},
                    start_date=None,
                    end_date=None,
                    aggregations={},
                    group_by=[]
                )
                # Add a dummy report_date column for compatibility
                filter_data['report_date'] = pd.Timestamp.now()
            except Exception as e2:
                st.error(f"Could not load filter data: {e2}")
                filter_data = pd.DataFrame()
        
        st.session_state.filter_data = filter_data
    
    # Get the filter data
    filter_df = st.session_state.filter_data
    
    # Step 1: Brand
    brand_list = get_filtered_list("Brand", TABLE_NAME)
    selected_brand = st.selectbox("Select Brand", ["All"] + brand_list)
    if selected_brand != "All":
        active_filters["Brand"] = selected_brand

    # Step 2: Campaign Code
    campaign_list = get_filtered_list("Campaign_code", TABLE_NAME, filters=active_filters)
    selected_campaign = st.selectbox("Select Campaign Code", campaign_list)  # No "All" as requested
    if selected_campaign:
        active_filters["Campaign_code"] = selected_campaign

    # Step 3: Date Range (based on the above)
    min_date, max_date = get_filtered_date_range(TABLE_NAME, filters=active_filters)
    if not min_date or not max_date:
        st.warning("No data found for the current Brand/Campaign selection.")
        st.stop()
    start_date, end_date = get_date_input(min_date, max_date)
    
    # Helper function to get filtered options from DataFrame
    def get_filtered_options(column_name, current_filters):
        """Get filtered options from DataFrame based on current filters"""
        if filter_df.empty:
            return []
        
        # Apply filters to DataFrame
        filtered_df = filter_df.copy()
        
        # Apply Brand filter
        if current_filters.get("Brand") and current_filters["Brand"] != "All":
            filtered_df = filtered_df[filtered_df["Brand"] == current_filters["Brand"]]
        
        # Apply Campaign filter
        if current_filters.get("Campaign_code") and current_filters["Campaign_code"] != "All":
            filtered_df = filtered_df[filtered_df["Campaign_code"] == current_filters["Campaign_code"]]
        
        # Apply Date filter
        if start_date and end_date:
            try:
                # Convert report_date column to datetime for proper comparison
                filtered_df["report_date"] = pd.to_datetime(filtered_df["report_date"])
                filtered_df = filtered_df[
                    (filtered_df["report_date"] >= pd.to_datetime(start_date)) & 
                    (filtered_df["report_date"] <= pd.to_datetime(end_date))
                ]
            except Exception as e:
                st.warning(f"Date filtering error: {e}. Showing all options for {column_name}.")
                # If date filtering fails, continue without date filter
        
        # Apply Platform filter
        if current_filters.get("Platform") and current_filters["Platform"] != "All":
            filtered_df = filtered_df[filtered_df["Platform"] == current_filters["Platform"]]
        
        # Apply Funnel filter
        if current_filters.get("Funnel") and current_filters["Funnel"] != "All":
            filtered_df = filtered_df[filtered_df["Funnel"] == current_filters["Funnel"]]
        
        # Apply Format filter
        if current_filters.get("Format") and current_filters["Format"] != "All":
            filtered_df = filtered_df[filtered_df["Format"] == current_filters["Format"]]
        
        # Apply Region filter
        if current_filters.get("Region") and current_filters["Region"] != "All":
            filtered_df = filtered_df[filtered_df["Region"] == current_filters["Region"]]
        
        # Apply Audience filter
        if current_filters.get("Audience") and current_filters["Audience"] != "All":
            filtered_df = filtered_df[filtered_df["Audience"] == current_filters["Audience"]]
        
        # Apply Buying_Method filter
        if current_filters.get("Buying_Method") and current_filters["Buying_Method"] != "All":
            filtered_df = filtered_df[filtered_df["Buying_Method"] == current_filters["Buying_Method"]]
        
        # Get unique values for the requested column
        if column_name in filtered_df.columns:
            return sorted(filtered_df[column_name].dropna().unique().tolist())
        return []
    
    # Step 4: Platform (inherits Brand + Campaign + Date)
    platform_options = get_filtered_options("Platform", {"Brand": active_filters.get("Brand"), "Campaign_code": active_filters.get("Campaign_code")})
    selected_platform = st.selectbox("Select Platform", ["All"] + platform_options)
    if selected_platform != "All":
        active_filters["Platform"] = selected_platform

    # Step 5: Funnel (inherits Brand + Campaign + Date + Platform)
    funnel_options = get_filtered_options("Funnel", {"Brand": active_filters.get("Brand"), "Campaign_code": active_filters.get("Campaign_code"), "Platform": active_filters.get("Platform")})
    selected_funnel = st.selectbox("Select Funnel", ["All"] + funnel_options)
    if selected_funnel != "All":
        active_filters["Funnel"] = selected_funnel

    # Step 6: Format (inherits Brand + Campaign + Date + Platform + Funnel)
    format_options = get_filtered_options("Format", {"Brand": active_filters.get("Brand"), "Campaign_code": active_filters.get("Campaign_code"), "Platform": active_filters.get("Platform"), "Funnel": active_filters.get("Funnel")})
    selected_format = st.selectbox("Select Format", ["All"] + format_options)
    if selected_format != "All":
        active_filters["Format"] = selected_format

    # Step 7: Region (inherits Brand + Campaign + Date + Platform + Funnel + Format)
    region_options = get_filtered_options("Region", {"Brand": active_filters.get("Brand"), "Campaign_code": active_filters.get("Campaign_code"), "Platform": active_filters.get("Platform"), "Funnel": active_filters.get("Funnel"), "Format": active_filters.get("Format")})
    selected_region = st.selectbox("Select Region", ["All"] + region_options)
    if selected_region != "All":
        active_filters["Region"] = selected_region

    # Step 8: Audience (inherits Brand + Campaign + Date + Platform + Funnel + Format + Region)
    audience_options = get_filtered_options("Audience", {"Brand": active_filters.get("Brand"), "Campaign_code": active_filters.get("Campaign_code"), "Platform": active_filters.get("Platform"), "Funnel": active_filters.get("Funnel"), "Format": active_filters.get("Format"), "Region": active_filters.get("Region")})
    selected_audience = st.selectbox("Select Audience", ["All"] + audience_options)
    if selected_audience != "All":
        active_filters["Audience"] = selected_audience

    # Step 9: Buying_Method (inherits Brand + Campaign + Date + Platform + Funnel + Format + Region + Audience)
    # Use get_filtered_list like other filters to ensure it works
    buying_method_options = get_filtered_list("Buying_Method", TABLE_NAME, filters=active_filters)
    selected_buying_method = st.selectbox("Select Buying Method", ["All"] + buying_method_options)
    if selected_buying_method != "All":
        active_filters["Buying_Method"] = selected_buying_method
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
# elif selected == "Test Overall":
#     display_tab_with_loading("Test Overall", test_overall.display, query_data, active_filters, start_date, end_date)
elif selected == "Test Overall Enhanced":
    display_tab_with_loading("Test Overall Enhanced", test_overall_enhanced.display, query_data, active_filters, start_date, end_date)

elif selected == "Test Table":
    display_tab_with_loading("Test Table", test_table.display, query_data, active_filters, start_date, end_date)
