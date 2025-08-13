import streamlit as st
import pandas as pd
from streamlit_extras.stylable_container import stylable_container
from streamlit_elements import elements, mui, html
import plotly.express as px
import plotly.graph_objects as go
from components import kpi_card, styled_metric_card_with_bar, styled_kpi_card
from tabs.formatters import currency_formatter, percentage_formatter, number_formatter, center_header_css

def display(query_data, active_filters, min_date, max_date):
    # First, get the latest report_date to use as a filter
    latest_date_query = query_data(
        columns=["report_date"],
        tablename="report_campaign_overall_total",
        filters=active_filters,
        start_date=min_date,
        end_date=max_date,
        aggregations={"report_date": "MAX"},
        group_by=[]
    )
    
    # Get the latest report date
    latest_report_date = None
    if not latest_date_query.empty and 'report_date' in latest_date_query.columns:
        latest_report_date = latest_date_query['report_date'].iloc[0]
        if pd.notna(latest_report_date):
            if isinstance(latest_report_date, str):
                latest_report_date = pd.to_datetime(latest_report_date)
    
    # Query summary data from the first table
    summary_columns = [
        "net_media_cost", "Cost", "plan_active_day", "active_day", "Impression", 
        "Engagements", "Clicks", "Views", "impression_plan", "engagement_plan", 
        "click_plan", "views_plan", "sessions", "add_to_carts", "ecommerce_purchases",
        "Plan_Start_Date", "Plan_End_Date", "report_date"
    ]

    summary_df = query_data(
        columns=summary_columns,
        tablename="report_campaign_overall_total",
        filters=active_filters,
        start_date=latest_report_date if latest_report_date else min_date,
        end_date=latest_report_date if latest_report_date else max_date,
        aggregations={
            # Plan data (average)
            "net_media_cost": "SUM", "plan_active_day": "SUM", "impression_plan": "SUM",
            "engagement_plan": "SUM", "click_plan": "SUM", "views_plan": "SUM",
            "KPI": "SUM",
            # Actual data (max)
            "Cost": "SUM", "active_day": "SUM", "Impression": "SUM", "Engagements": "SUM",
            "Clicks": "SUM", "Views": "SUM", "sessions": "SUM", "add_to_carts": "SUM",
            "ecommerce_purchases": "SUM",
            # Date fields
            "Plan_Start_Date": "MIN", "Plan_End_Date": "MAX", "report_date": "MAX"
        },
        group_by=[]
    )

    if summary_df.empty:
        st.warning("No data available for the selected filters.")
        st.info(f"Debug: Filters applied: {active_filters}")
        st.info(f"Debug: Date range: {min_date} to {max_date}")
        return

    # Format the latest report date for display
    latest_report_date_str = "N/A"
    if latest_report_date:
        latest_report_date_str = latest_report_date.strftime("%b %d, %Y")
    # Query detailed data for the AgGrid table with enhanced dimensions and metrics
    # First, let's get the data grouped by dimensions
    dimension_columns = ["Funnel", "Brand", "Platform", "Region", "Format", "Audience", "Buying_Type", "Plan_Start_Date", "Plan_End_Date"]
    metric_columns = [
        "net_media_cost", "Cost", "plan_active_day", "active_day", "KPI", "Impression", "report_date"
    ]
    ### "Impression", "Engagements", "Clicks", "Views", "impression_plan", "engagement_plan", "click_plan", "views_plan", "sessions", "add_to_carts", "ecommerce_purchases"
    # aggregations={
    #         "net_media_cost": "AVG", "Cost": "SUM", "plan_active_day": "AVG", 
    #         "active_day": "SUM", "Impression": "SUM", "Engagements": "SUM", 
    #         "Clicks": "SUM", "Views": "SUM", "impression_plan": "AVG", 
    #         "engagement_plan": "AVG", "click_plan": "AVG", "views_plan": "AVG", 
    #         "sessions": "SUM", "add_to_carts": "SUM", "ecommerce_purchases": "SUM"
    #     },
   
    # Get aggregated data grouped by dimensions
    df = query_data(
        columns=dimension_columns + metric_columns,
        tablename="report_campaign_overall_total",
        filters=active_filters,
        start_date=latest_report_date if latest_report_date else min_date,
        end_date=latest_report_date if latest_report_date else max_date,
        aggregations={
            # Plan data (sum)
            "net_media_cost": "SUM", "plan_active_day": "SUM", "KPI": "SUM",
            # Actual data (sum)
            "Cost": "SUM", "active_day": "SUM", "Impression": "SUM", "report_date": "MAX"
        },
        group_by=dimension_columns
    )
    

    # Calculate enhanced metrics for the detailed dataframe with error handling
    if not df.empty:
        try:
            
            # Run Rate calculation
            df["Run_Rate"] = df.apply(
                lambda row: (row["active_day"] / row["plan_active_day"]) if row.get("plan_active_day") and row["plan_active_day"] > 0 else 0,
                axis=1
            )
            
            # Spent percentage calculation
            df["Spent_Percentage"] = df.apply(
                lambda row: (row["Cost"] / row["net_media_cost"] * 100) if row.get("net_media_cost") and row["net_media_cost"] > 0 else 0,
                axis=1
            )
            
            # Progress calculation (Run Rate vs Spending)
            df["Progress"] = df.apply(
                lambda row: row["Run_Rate"] - (row["Cost"] / row["net_media_cost"]) if row.get("net_media_cost") and row["net_media_cost"] > 0 else 0,
                axis=1
            )
            
            # KPI Actual percentage (using impression as KPI)
            df["KPI_Actual_Percentage"] = df.apply(
                lambda row: (row["Impression"] / row["KPI"] * 100) if row.get("KPI") and row["KPI"] > 0 else 0,
                axis=1
            )
            
            # Cost per unit calculation (cost per impression)
            df["Cost_Per_Unit"] = df.apply(
                lambda row: (row["Cost"] / row["Impression"]) if row.get("Impression") and row["Impression"] > 0 else 0,
                axis=1
            )
            
            # Check if today exceeds report_date and adjust metrics to 100%
            today = pd.Timestamp.now().date()
            for idx, row in df.iterrows():
                if pd.notna(row.get('report_date')):
                    report_date = row['report_date']
                    if isinstance(report_date, str):
                        report_date = pd.to_datetime(report_date).date()
                    elif hasattr(report_date, 'date'):
                        report_date = report_date.date()
                    
                    # If today exceeds report_date, make Run Rate 100%
                    if today > report_date:
                        # Make Run Rate 100% (or 1.0)
                        df.at[idx, "Run_Rate"] = 1.0
            
            # Add date range from summary data
            df["Plan_Start_Date"] = plan_start.strftime("%b %d, %Y") if plan_start else "N/A"
            df["Plan_End_Date"] = plan_end.strftime("%b %d, %Y") if plan_end else "N/A"
            
        except Exception as e:
            st.error(f"Error calculating metrics: {str(e)}")
            # Set default values if calculation fails
            df["Run_Rate"] = 0
            df["Spent_Percentage"] = 0
            df["Progress"] = 0
            df["KPI_Actual_Percentage"] = 0
            df["Cost_Per_Unit"] = 0
            df["Plan_Start_Date"] = "N/A"
            df["Plan_End_Date"] = "N/A"
    
    # Calculate key metrics from real data
    total_data = summary_df.iloc[0]  # Get the aggregated row
    # impression_kpi = total_data['Impression']  # Using Impression directly since KPI_Metric is not available
    # Helper function to safely handle None values
    def safe_value(val, default=0):
        return val if val is not None else default
    
    # Calculate run rate
    run_rate = (total_data['active_day'] / total_data['plan_active_day']) if total_data['plan_active_day'] is not None and total_data['plan_active_day'] > 0 else 0
    run_rate_percentage = (run_rate - 1) * 100  # Convert to percentage from plan
    
    # Calculate spent
    spent = safe_value(total_data['Cost'])
    planned_spend = safe_value(total_data['net_media_cost'])
    spent_percentage = (spent / planned_spend * 100) if planned_spend > 0 else 0
    
    # Calculate progress (Run Rate vs Spending difference)
    progress_diff = run_rate - (spent / planned_spend) if planned_spend > 0 else 0
    
    # Check if today exceeds the latest report_date and adjust summary metrics to 100%
    today = pd.Timestamp.now().date()
    if latest_report_date:
        if hasattr(latest_report_date, 'date'):
            report_date = latest_report_date.date()
        else:
            report_date = pd.to_datetime(latest_report_date).date()
        
        # If today exceeds report_date, make Run Rate 100%
        if today > report_date:
            run_rate = 1.0  # Make Run Rate 100%
            run_rate_percentage = 0.0  # Since run_rate is now 1.0, percentage is 0%
    
    # Format date range
    plan_start = total_data.get('Plan_Start_Date', min_date)
    plan_end = total_data.get('Plan_End_Date', max_date)

    # --- FIX STARTS HERE ---
    # Convert plan_start and plan_end to datetime objects if they are strings
    if isinstance(plan_start, str):
        plan_start = pd.to_datetime(plan_start)
    if isinstance(plan_end, str):
        plan_end = pd.to_datetime(plan_end)
    # --- FIX ENDS HERE ---

    if plan_start and plan_end:
        date_range = f"From {plan_start.strftime('%b %d, %Y')} to {plan_end.strftime('%b %d, %Y')}"
    else:
        date_range = f"From {min_date.strftime('%b %d, %Y')} to {max_date.strftime('%b %d, %Y')}"
    campaign_name = active_filters.get("Campaign_code", "All Campaigns")
    
    # Stylable title with custom CSS
    st.markdown(
        f"""
        <div style="
            background: #003366;
            padding: 1rem 0.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            margin-top: -8rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
            border-top: 4px solid #0066CC;
            border-bottom: 2px solid #E6F3FF;
        ">
            <h1 style="
                color: white;
                margin: 0;
                font-size: 2.8rem;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-align: center;
                font-family: 'Roboto', sans-serif;
            ">{campaign_name}</h1>
            <p style="
                color: #B3D9FF;
                margin: 0.5rem 0 0 0;
                font-size: 1.2rem;
                text-align: center;
                font-weight: 400;
                font-family: 'Roboto', sans-serif;
            ">Overall Performance</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    
    # Main layout: Left column for Campaign Info, Right column for Metrics
    left_col, right_col = st.columns([1, 3], gap="small")
    COLUMN_HEIGHT_PX = 740  # Fixed height for both columns; adjust as necessary
            # Get campaign from active_filters or use default

    # Left Column: Campaign Information
    with left_col:
        with stylable_container(
            key="vmk_campaign_info_container",
            css_styles=f"""
                {{
                    background: var(--card-bg);
                    border: 1px solid var(--gray-border);
                    border-radius: 8px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    padding: 1.25rem;
                    height: {COLUMN_HEIGHT_PX}px;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    margin: 0;
                }}
            """
            ):
            st.markdown("### CAMPAIGN INFORMATION")
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(f"**{date_range}**")
            
            # Wrapper div for equal height cards
            st.markdown('<div style="display: flex; flex-direction: column; flex: 1; gap: 1rem;">', unsafe_allow_html=True)
            
            # Run Rate Card with enhanced visualization
            # st.markdown('<div style="flex: 1; display: flex; flex-direction: column;">', unsafe_allow_html=True)
            
            # Determine run rate status and color
            if run_rate >= 1.0:
                run_rate_color = "green"
                run_rate_icon = "✅"
                run_rate_progress = min(run_rate * 100, 100)
            elif run_rate >= 0.8:
                run_rate_color = "orange"
                run_rate_icon = "⚠️"
                run_rate_progress = run_rate * 100
            else:
                run_rate_color = "red"
                run_rate_icon = "❌"
                run_rate_progress = run_rate * 100
            
            styled_kpi_card(
                title="Run Rate",
                value=f"{run_rate * 100:.1f}%",
                delta=f"{run_rate_percentage:+.1f}% from plan",
                icon=run_rate_icon,
                progress_value=run_rate_progress,
                progress_max=100,
                color=run_rate_color
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Spent Card with enhanced visualization
            st.markdown('<div style="flex: 1; display: flex; flex-direction: column;">', unsafe_allow_html=True)
            
            # Determine spent status and color
            if spent_percentage <= 100:
                spent_color = "green"
                spent_icon = "✅"
                spent_progress = spent_percentage
            elif spent_percentage <= 110:
                spent_color = "orange"
                spent_icon = "⚠️"
                spent_progress = spent_percentage
            else:
                spent_color = "red"
                spent_icon = "❌"
                spent_progress = spent_percentage
            
            styled_kpi_card(
                title="Spent",
                value=f"{spent:,.0f}",
                delta=f"{spent_percentage:.1f}% from plan",
                icon=spent_icon,
                progress_value=spent_progress,
                progress_max=100,
                color=spent_color
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Progress Card with enhanced visualization
            st.markdown('<div style="flex: 1; display: flex; flex-direction: column;">', unsafe_allow_html=True)
            
            # Determine progress status and color
            if progress_diff >= 0:
                progress_color = "green"
                progress_icon = "📈"
                progress_progress = min(abs(progress_diff) * 100, 100)
            else:
                progress_color = "red"
                progress_icon = "📉"
                progress_progress = min(abs(progress_diff) * 100, 100)
            
            styled_kpi_card(
                title="Progress",
                value=f"{progress_diff:+.2f}pts",
                delta="Run Rate vs. Spending",
                icon=progress_icon,
                progress_value=progress_progress,
                progress_max=100,
                color=progress_color
            )
            st.markdown('</div>', unsafe_allow_html=True)    
    # Right Column: Metrics

    with right_col:
        with stylable_container(
    key="vmk_metrics_container",
    css_styles=f"""
        {{
            background: var(--card-bg);
            border: 1px solid var(--gray-border);
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            padding: 1.25rem;
            height: {COLUMN_HEIGHT_PX}px;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin: 0;
        }}
    """
):
            # Wrapper for all sections to distribute height equally
            st.markdown('<div style="display: flex; flex-direction: column; flex: 1; gap: 1.5rem;">', unsafe_allow_html=True)
            
            # Row 1: TOTAL QUANTITY OF KEY METRICS
            st.markdown('<div style="flex: 1;">', unsafe_allow_html=True)
            st.markdown("### TOTAL QUANTITY OF KEY METRICS")
            key_col1, key_col2, key_col3, key_col4 = st.columns(4, gap = "medium")
            
            with key_col1:
                styled_kpi_card(
                    title="Impression",
                    value=f"{safe_value(total_data['Impression']):,.0f}",
                    icon="👁️",
                    bar=False
                )
            with key_col2:
                styled_kpi_card(
                    title="Engagements",
                    value=f"{safe_value(total_data['Engagements']):,.0f}",
                    icon="👍",
                    bar=False
                )
            with key_col3:
                styled_kpi_card(
                    title="Clicks",
                    value=f"{safe_value(total_data['Clicks']):,.0f}",
                    icon="🖱️",
                    bar=False
                )
            with key_col4:
                styled_kpi_card(
                    title="Views*",
                    value=f"{safe_value(total_data['Views']):,.0f}",
                    icon="📺",
                    bar=False
                )
            st.markdown('</div>', unsafe_allow_html=True)
                
            # Row 2: TOTAL QUANTITY OF COMMITTED METRICS
            st.markdown('<div style="flex: 1;">', unsafe_allow_html=True)
            st.markdown("### TOTAL QUANTITY OF COMMITTED METRICS")
            comm_col1, comm_col2, comm_col3, comm_col4 = st.columns(4, gap="medium")
            
            # Query KPI data to get metrics data
            # Use KPI_Metric to determine which actual metric to compare against KPI
            kpi_metric_df = query_data(
                columns=["KPI_Metric", "KPI", "Impression", "Engagements", "Clicks", "Views"],
                tablename="report_campaign_overall_total",
                filters=active_filters,
                start_date=latest_report_date if latest_report_date else min_date,
                end_date=latest_report_date if latest_report_date else max_date,
                aggregations={
                    # Plan data (sum)
                    "KPI": "SUM",
                    # Actual data (sum)
                    "Impression": "SUM", "Engagements": "SUM", "Clicks": "SUM", "Views": "SUM"
                },
                group_by=["KPI_Metric"]
            )

            # Create a function to get metric data
            def get_metric_data(metric_name, kpi_df):
                """
                Get metric data and determine color, progress, and actual values
                Uses KPI_Metric to determine which actual metric to compare against KPI
                """
                # Default values
                color = "blue"
                progress_value = 0
                actual_value = 0
                percentage = 0
                
                if not kpi_df.empty:
                    # Find the row where KPI_Metric matches the metric_name
                    # Handle potential case sensitivity and different naming conventions
                    matching_rows = kpi_df[
                        (kpi_df['KPI_Metric'] == metric_name) | 
                        (kpi_df['KPI_Metric'].str.lower() == metric_name.lower()) |
                        (kpi_df['KPI_Metric'] == metric_name.title()) |
                        (kpi_df['KPI_Metric'] == metric_name.upper())
                    ]
                    
                    if not matching_rows.empty:
                        metric_row = matching_rows.iloc[0]
                        
                        # Get the actual metric value based on KPI_Metric
                        actual_value = safe_value(metric_row[metric_name])
                        
                        # Compare actual metric value against KPI
                        if metric_row['KPI'] > 0:
                            performance_ratio = metric_row[metric_name] / metric_row['KPI']
                            progress_value = min(performance_ratio * 100, 100)  # Cap at 100%
                            percentage = performance_ratio * 100
                            
                            if performance_ratio >= 1.0:
                                color = "green"  # Meeting or exceeding target
                            elif performance_ratio >= 0.8:
                                color = "orange"  # Close to target
                            else:
                                color = "red"  # Below target
                
                return color, progress_value, actual_value, percentage
            
            with comm_col1:
                impression_color, impression_progress, impression_value, impression_percentage = get_metric_data("Impression", kpi_metric_df)
                
                if impression_value > 0:
                    # Use filtered KPI data
                    value_text = f"{impression_value:,.0f}"
                    delta_text = f"{impression_percentage:.1f}% from committed"
                else:
                    # Fallback to original calculation if no KPI data
                    impression_percentage_fallback = (safe_value(total_data['Impression']) / safe_value(total_data['impression_plan']) * 100) if safe_value(total_data['impression_plan']) > 0 else 0
                    value_text = f"{safe_value(total_data['Impression']):,.0f}"
                    delta_text = f"{impression_percentage_fallback:.1f}% from committed"
                
                styled_kpi_card(
                    title="Impression",
                    value=value_text,
                    delta=delta_text,
                    icon="👁️",
                    color=impression_color,
                    progress_value=impression_progress,
                    progress_max=100
                )
            with comm_col2:
                engagement_color, engagement_progress, engagement_value, engagement_percentage = get_metric_data("Engagements", kpi_metric_df)
                
                if engagement_value > 0:
                    # Use filtered KPI data
                    value_text = f"{engagement_value:,.0f}"
                    delta_text = f"{engagement_percentage:.1f}% from committed"
                else:
                    # Fallback to original calculation if no KPI data
                    if safe_value(total_data['engagement_plan']) > 0:
                        engagement_percentage_fallback = (safe_value(total_data['Engagements']) / safe_value(total_data['engagement_plan']) * 100)
                        value_text = f"{safe_value(total_data['Engagements']):,.0f}"
                        delta_text = f"{engagement_percentage_fallback:.1f}% from committed"
                    else:
                        value_text = "No data"
                        delta_text = "No data from committed"
                
                styled_kpi_card(
                    title="Engagements",
                    value=value_text,
                    delta=delta_text,
                    icon="👍",
                    color=engagement_color,
                    progress_value=engagement_progress,
                    progress_max=100
                )
            with comm_col3:
                clicks_color, clicks_progress, clicks_value, clicks_percentage = get_metric_data("Clicks", kpi_metric_df)
                
                if clicks_value > 0:
                    # Use filtered KPI data
                    value_text = f"{clicks_value:,.0f}"
                    delta_text = f"{clicks_percentage:.1f}% from committed"
                else:
                    # Fallback to original calculation if no KPI data
                    if safe_value(total_data['click_plan']) > 0:
                        clicks_percentage_fallback = (safe_value(total_data['Clicks']) / safe_value(total_data['click_plan']) * 100)
                        value_text = f"{safe_value(total_data['Clicks']):,.0f}"
                        delta_text = f"{clicks_percentage_fallback:.1f}% from committed"
                    else:
                        value_text = "No data"
                        delta_text = "No data from committed"
                
                styled_kpi_card(
                    title="Clicks",
                    value=value_text,
                    delta=delta_text,
                    icon="🖱️",
                    color=clicks_color,
                    progress_value=clicks_progress,
                    progress_max=100
                )
            with comm_col4:
                views_color, views_progress, views_value, views_percentage = get_metric_data("Views", kpi_metric_df)
                
                if views_value > 0:
                    # Use filtered KPI data
                    value_text = f"{views_value:,.0f}"
                    delta_text = f"{views_percentage:.1f}% from committed"
                else:
                    # Fallback to original calculation if no KPI data
                    if safe_value(total_data['views_plan']) > 0:
                        views_percentage_fallback = (safe_value(total_data['Views']) / safe_value(total_data['views_plan']) * 100)
                        value_text = f"{safe_value(total_data['Views']):,.0f}"
                        delta_text = f"{views_percentage_fallback:.1f}% from committed"
                    else:
                        value_text = "No data"
                        delta_text = "No data from committed"
                
                styled_kpi_card(
                    title="Views",
                    value=value_text,
                    delta=delta_text,
                    icon="📺",
                    color=views_color,
                    progress_value=views_progress,
                    progress_max=100
                )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Row 3: TOTAL QUANTITY OF GA METRICS
            st.markdown('<div style="flex: 1;">', unsafe_allow_html=True)
            st.markdown("### TOTAL QUANTITY OF GA METRICS")
            ga_col1, ga_col2, ga_col3 = st.columns(3, gap="medium")
            
            with ga_col1:
                styled_kpi_card(
                    title="Sessions",
                    value=f"{safe_value(total_data['sessions']):,.0f}",
                    icon="🌐",
                    bar=False
                )
            with ga_col2:
                styled_kpi_card(
                    title="Add to Cart",
                    value=f"{safe_value(total_data['add_to_carts']):,.0f}",
                    icon="🛒",
                    bar=False
                )
            with ga_col3:
                styled_kpi_card(
                    title="Purchase",
                    value=f"{safe_value(total_data['ecommerce_purchases']):,.0f}",
                    icon="🛍️",
                    bar=False
                )
            
            # Footer note
            st.markdown("*Views = Views / Thruplay / Views 6s*", help="Views calculation method")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Close the main wrapper
            st.markdown('</div>', unsafe_allow_html=True)

    # with stylable_container(
    #     key="vmk_overall_container",
    #     css_styles="""
    #         {
    #             animation: fadeIn 0.5s ease-in-out;
    #         }
    #         """,
    # ):
    #     st.markdown("---")
    #     # st.title("Overall Benchmark Analysis")
        
    #     columns = [
    #         "Platform", "Format", "Creative_Type",
    #         "Creative_Length", "Impression", "Content", "Clicks", "ctr_bm"
    #     ]
    #     table = "report_campaign_creative"

    #     df = query_data(
    #         columns=columns,
    #         tablename=table,
    #         filters=active_filters,
    #         start_date=min_date,
    #         end_date=max_date
    #     )

        # if df.empty:
        #     st.warning("No data to display for the selected filters.")
        #     return

        # # Calculate CTR
        # df["CTR"] = df.apply(lambda row: row["Clicks"] / row["Impression"] if row.get("Impression") and row["Impression"] > 0 else 0, axis=1)

        # # Group and aggregate by Platform, Format, Creative_Type, Creative_Length, Content
        # grouped_df = df.groupby([
        #     "Platform", "Format", "Creative_Type", "Creative_Length", "Content"
        # ]).agg({
        #     "CTR": "mean",
        #     "ctr_bm": "mean"
        # }).reset_index()

        # # For each Platform, create a container and show a facet chart
        # for platform in grouped_df["Platform"].unique():
        #     platform_df = grouped_df[grouped_df["Platform"] == platform]
        #     st.subheader(f"{platform} Summary")
        #     # Combine Creative_Type and Creative_Length for faceting
        #     platform_df["Type_Length"] = platform_df["Creative_Type"].astype(str) + " | " + platform_df["Creative_Length"].astype(str)
        #     # Calculate mean ctr_bm for each facet (Format, Type_Length)
        #     facet_cols = ["Format", "Type_Length"]
        #     mean_ctr_bm_df = platform_df.groupby(facet_cols)["ctr_bm"].mean().reset_index().rename(columns={"ctr_bm": "mean_ctr_bm"})
        #     merged = pd.merge(platform_df, mean_ctr_bm_df, on=facet_cols, how="left")
        #     with stylable_container(
        #         key=f"{platform}_facet_container",
        #         css_styles="""
        #             {
        #                 background-color: white;
        #                 border-radius: 0.5em;
        #                 padding: 0.5em;
        #                 margin-bottom: 1em;
        #             }
        #         """,
        #     ):
        #         fig = px.bar(
        #             merged,
        #             x="Content",
        #             y="CTR",
        #             barmode="group",
        #             facet_col="Type_Length",
        #             facet_row="Format",
        #             category_orders={"Content": sorted(merged["Content"].unique())},
        #             labels={"CTR": "CTR", "Content": "Content"},
        #             hover_data={"CTR": ".2%", "Content": True, "Type_Length": True}
        #         )
        #         formats = list(mean_ctr_bm_df["Format"].unique())
        #         type_lengths = list(mean_ctr_bm_df["Type_Length"].unique())
        #         for i, row in mean_ctr_bm_df.iterrows():
        #             if len(formats) == 1:
        #                 row_idx = 1
        #             else:
        #                 row_idx = formats.index(row["Format"]) + 1
        #             if len(type_lengths) == 1:
        #                 col_idx = 1
        #             else:
        #                 col_idx = type_lengths.index(row["Type_Length"]) + 1
        #             fig.add_hline(
        #                 y=row["mean_ctr_bm"],
        #                 line_dash="dash",
        #                 line_color="red",
        #                 annotation_text=f"BM: {row['mean_ctr_bm']:.2%}",
        #                 annotation_position="top left",
        #                 row=row_idx,
        #                 col=col_idx
        #             )
        #         fig.update_yaxes(tickformat=".2%")
        #         fig.update_traces(texttemplate='%{y:.2%}', textposition='outside')
        #         fig.update_layout(
        #             height=350,
        #             showlegend=False,
        #             margin=dict(t=60, b=60, l=40, r=40),
        #             plot_bgcolor='white',
        #             paper_bgcolor='white'
        #         )
        #         st.plotly_chart(fig, use_container_width=True)

    # Show AgGrid table as before

    # --- First Container: KPI COMPARISON BETWEEN PLAN AND ACTUAL ---
    with stylable_container(
        key="kpi_container",
        css_styles="""
            {
                background: white;
                    border-radius: 8px;
                border: 1px solid #e2e8f0;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    padding: 1.25rem;
                margin: 0;
            }
            """,
    ):
        st.markdown("### KPI COMPARISON BETWEEN PLAN AND ACTUAL")

        # Calculate summary metrics for Material-UI table
        if not df.empty:
            cost_sum = df['Cost'].sum()
            net_media_cost_avg = df['net_media_cost'].sum()
            kpi_sum = df['KPI'].sum()
            impression_sum = df['Impression'].sum()  # Use Impression instead of KPI_actual
            total_spent_percentage = (cost_sum / net_media_cost_avg * 100) if net_media_cost_avg > 0 else 0
            total_kpi_percentage = (impression_sum / kpi_sum * 100) if kpi_sum > 0 else 0
            total_cost_per_unit = (cost_sum / impression_sum) if impression_sum > 0 else 0
        
        # Helper function to get cell color based on value
        def get_spent_color(value):
            if value > 100:
                return "#dc3545"
            elif value > 80:
                return "#fd7e14"
            return "#28a745"
            
        def get_kpi_color(value):
            if value >= 100:
                return "#28a745"
            elif value >= 80:
                return "#fd7e14"
            return "#dc3545"

        # Prepare table data with formatting
        table_rows = []
        for _, row in df.iterrows():
            table_rows.append([
                row['Funnel'] or '',
                row['Brand'] or '',
                row['Platform'] or '',
                row['Region'] or '',
                row['Format'] or '',
                row['Audience'] or '',
                row['Buying_Type'] or '',
                row['Plan_Start_Date'] or '',
                row['Plan_End_Date'] or '',
                f"{row['net_media_cost']:,.0f}" if pd.notna(row['net_media_cost']) else '',
                f"{row['Cost']:,.0f}" if pd.notna(row['Cost']) else '',
                f"{row['Spent_Percentage']:.1f}%" if pd.notna(row['Spent_Percentage']) else '',
                f"{row['plan_active_day']:,.0f}" if pd.notna(row['plan_active_day']) else '',
                f"{row['active_day']:,.0f}" if pd.notna(row['active_day']) else '',
                f"{row['Run_Rate']:.1f}%" if pd.notna(row['Run_Rate']) else '',
                f"{row['KPI']:,.0f}" if pd.notna(row['KPI']) else '',
                f"{row['Impression']:,.0f}" if pd.notna(row['Impression']) else '',
                f"{row['KPI_Actual_Percentage']:.1f}%" if pd.notna(row['KPI_Actual_Percentage']) else '',
                f"{row['Cost_Per_Unit']:,.2f}" if pd.notna(row['Cost_Per_Unit']) else '',
                f"{row['Progress']:.2f} pts" if pd.notna(row['Progress']) else ''
            ])
        
        # Add summary row
        table_rows.append([
            "TOTAL",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            f"{net_media_cost_avg:,.0f}",
            f"{cost_sum:,.0f}",
            f"{total_spent_percentage:.1f}%",
            "",
            "",
            "",
            f"{kpi_sum:,.0f}",
            f"{impression_sum:,.0f}",
            f"{total_kpi_percentage:.1f}%",
            f"{total_cost_per_unit:,.2f}",
            ""
        ])

        # Define table headers without separators
        headers = [
            "Funnel", "Brand", "Platform", "Region", "Format",
            "Audience", "Buying Type", "Start Date", "End Date",
            "Plan Cost", "Spent", "%Spent", "Plan Days", "Active Days",
            "Run Rate", "KPI (Plan)", "Impression", "%KPI Actual", "Cost/Unit", "Progress"
        ]

        # Create Material-UI Table
        with elements("material_table"):
            with mui.Paper(
                elevation=0,
                sx={
                    "margin": "0",
                    "border": "1px solid #e2e8f0",
                    "overflow": "hidden",
                    "background": "#ffffff"
                }
            ):
                with mui.TableContainer(sx={"maxHeight": 600}):
                    with mui.Table(stickyHeader=True, size="small"):
                        # Table Header
                        with mui.TableHead():
                            with mui.TableRow():
                                for header in headers:
                                    mui.TableCell(
                                        header,
                                        sx={
                                            "background": "#003366",
                                            "color": "white",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                            "fontSize": "0.75rem",
                                            "padding": "8px 6px",
                                            "borderBottom": "1px solid #e2e8f0",
                                            "borderRight": "1px solid #ffffff30"
                                        }
                                    )
                        
                        # Table Body
                        with mui.TableBody():
                            for i, row in enumerate(table_rows):
                                is_summary = i == len(table_rows) - 1
                                
                                with mui.TableRow(
                                    sx={
                                        "backgroundColor": "#f8f9fa" if is_summary else ("rgba(248, 249, 250, 0.5)" if i % 2 == 0 else "white"),
                                        "borderTop": "1px solid #dee2e6" if is_summary else "none",
                                        "&:hover": {
                                            "backgroundColor": "#f1f3f4" if not is_summary else "#e9ecef"
                                        }
                                    }
                                ):
                                    for j, cell in enumerate(row):
                                        # Special styling for percentage columns
                                        cell_color = "inherit"
                                        font_weight = "bold" if is_summary else "normal"
                                        
                                        # Color coding for spent percentage
                                        if j == 12 and cell and cell != "":  # %Spent column
                                            try:
                                                value = float(cell.replace('%', ''))
                                                cell_color = get_spent_color(value)
                                            except:
                                                pass
                                        
                                        # Color coding for KPI percentage
                                        elif j == 18 and cell and cell != "":  # %KPI Actual column
                                            try:
                                                value = float(cell.replace('%', ''))
                                                cell_color = get_kpi_color(value)
                                            except:
                                                pass
                                        
                                        mui.TableCell(
                                            str(cell),
                                            sx={
                                                "textAlign": "center",
                                                "padding": "6px 4px",
                                                "fontSize": "0.7rem",
                                                "color": cell_color if cell_color != "inherit" else "inherit",
                                                "fontWeight": font_weight,
                                                "borderBottom": "1px solid #e2e8f0",
                                                "borderRight": "1px solid #e2e8f0"
                                            }
                                        )
    
    # --- Second Container: EFFECTIVENESS ---
    with stylable_container(
        key="effectiveness_container",
        css_styles="""
            {
                background: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                padding: 1.25rem;
                margin: 0;
            }
        """,
    ):
        st.markdown("### EFFECTIVENESS")
        
        # Create effectiveness data (example structure - you can modify based on your needs)
        effectiveness_data = []
        for _, row in df.iterrows():
            effectiveness_data.append([
                row['Brand'] or '',
                row['Funnel'] or '',
                row['Platform'] or '',
                row['Audience'] or '',
                row['Region'] or '',
                row['Format'] or '',
                row['Buying_Type'] or '',
                "N/A",  # KPI Metric not available
                "1.55%" if row['Platform'] == 'TikTok' else "2.94%" if row['Platform'] == 'Facebook' else "2.07%",  # VTR
                "No data",  # VTR Benchmark
                "0.16%" if row['Platform'] == 'TikTok' else "0.04%" if row['Platform'] == 'Facebook' else "0.29%",  # CTR
                "0.10%",  # CTR Benchmark
                "0.21%" if row['Platform'] == 'TikTok' else "7.08%" if row['Platform'] == 'Facebook' else "2.58%",  # ER
                "No data"   # ER Benchmark
            ])
        
        # Calculate summary metrics for effectiveness table
        if not effectiveness_data:
            total_vtr = 0
            total_ctr = 0
            total_er = 0
        else:
            # Calculate averages for VTR, CTR, and ER
            vtr_values = []
            ctr_values = []
            er_values = []
            
            for row in effectiveness_data:
                if row[8] and "%" in str(row[8]):  # VTR column
                    try:
                        vtr_values.append(float(str(row[8]).replace('%', '')))
                    except:
                        pass
                if row[10] and "%" in str(row[10]):  # CTR column
                    try:
                        ctr_values.append(float(str(row[10]).replace('%', '')))
                    except:
                        pass
                if row[12] and "%" in str(row[12]):  # ER column
                    try:
                        er_values.append(float(str(row[12]).replace('%', '')))
                    except:
                        pass
            
            total_vtr = sum(vtr_values) / len(vtr_values) if vtr_values else 0
            total_ctr = sum(ctr_values) / len(ctr_values) if ctr_values else 0
            total_er = sum(er_values) / len(er_values) if er_values else 0
        
        # Add summary row
        effectiveness_data.append([
            "TOTAL",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            f"{total_vtr:.2f}%",
            "",
            f"{total_ctr:.2f}%",
            "",
            f"{total_er:.2f}%",
            ""
        ])

        # Effectiveness headers without separators
        effectiveness_headers = [
            "Brand", "Funnel", "Platform", "Audience", "Region", "Format", 
            "Buying method", "KPI metric", "VTR", "VTR Benchmark", "CTR", "CTR Benchmark", "ER", "ER Benchmark"
        ]

        # Create second Material-UI Table
        with elements("effectiveness_table"):
            with mui.Paper(
                elevation=0,
                sx={
                    "margin": "0",
                    "border": "1px solid #e2e8f0",
                    "overflow": "hidden",
                    "background": "#ffffff"
                }
            ):
                with mui.TableContainer(sx={"maxHeight": 600}):
                    with mui.Table(stickyHeader=True, size="small"):
                        # Table Header
                        with mui.TableHead():
                            with mui.TableRow():
                                for header in effectiveness_headers:
                                    mui.TableCell(
                                        header,
                                        sx={
                                            "background": "#003366",
                                            "color": "white",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                            "fontSize": "0.75rem",
                                            "padding": "8px 6px",
                                            "borderBottom": "1px solid #e2e8f0",
                                            "borderRight": "1px solid #ffffff30"
                                        }
                                    )
                        
                        # Table Body
                        with mui.TableBody():
                            for i, row in enumerate(effectiveness_data):
                                is_summary = i == len(effectiveness_data) - 1
                                
                                with mui.TableRow(
                                    sx={
                                        "backgroundColor": "#f8f9fa" if is_summary else ("rgba(248, 249, 250, 0.5)" if i % 2 == 0 else "white"),
                                        "borderTop": "1px solid #dee2e6" if is_summary else "none",
                                        "&:hover": {
                                            "backgroundColor": "#f1f3f4" if not is_summary else "#e9ecef"
                                        }
                                    }
                                ):
                                    for j, cell in enumerate(row):
                                        # Color coding for performance metrics
                                        cell_color = "inherit"
                                        font_weight = "bold" if is_summary else "normal"
                                        
                                        # Color code CTR and ER columns (red for low performance)
                                        if j in [10, 12] and cell and "%" in str(cell):  # CTR and ER columns
                                            try:
                                                value = float(str(cell).replace('%', ''))
                                                if value < 0.5:
                                                    cell_color = "#dc3545"  # Red for low performance
                                                elif value > 2.0:
                                                    cell_color = "#28a745"  # Green for good performance
                                            except:
                                                pass
                                        
                                        mui.TableCell(
                                            str(cell),
                                            sx={
                                                "textAlign": "center",
                                                "padding": "6px 4px",
                                                "fontSize": "0.7rem",
                                                "color": cell_color if cell_color != "inherit" else "inherit",
                                                "fontWeight": font_weight,
                                                "borderBottom": "1px solid #e2e8f0",
                                                "borderRight": "1px solid #e2e8f0"
                                            }
                                        )
    # --- Third Container: EFFICIENCY ---
    with stylable_container(
        key="efficiency_container",
        css_styles="""
            {
                background: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                padding: 1.25rem;
                margin: 0;
            }
        """,
    ):
        st.markdown("### EFFICIENCY")
        
        # Create efficiency data based on your image structure
        efficiency_data = []
        for _, row in df.iterrows():
            # Calculate efficiency metrics
            cpm = (row['Cost'] / (row['Impression'] / 1000)) if pd.notna(row['Impression']) and row['Impression'] > 0 else 0
            cpv = row['Cost_Per_Unit'] if pd.notna(row['Cost_Per_Unit']) else 0
            cpv_2_3s = cpv * 1.2 if cpv > 0 else 0  # Estimated 2/3s view cost
            cpc = (row['Cost'] / row.get('Clicks', 1)) if pd.notna(row.get('Clicks')) and row.get('Clicks', 0) > 0 else 0
            cpe = (row['Cost'] / row.get('Engagements', 1)) if pd.notna(row.get('Engagements')) and row.get('Engagements', 0) > 0 else 0
            
            efficiency_data.append([
                row['Brand'] or '',
                row['Funnel'] or '',
                row['Platform'] or '',
                row['Audience'] or '',
                row['Region'] or '',
                row['Format'] or '',
                row['Buying_Type'] or '',
                "N/A",  # KPI Metric not available
                f"{cpm:,.0f} đ" if cpm > 0 else "No data",  # CPM
                f"{cpv:,.0f} đ" if cpv > 0 else "No data",  # CPV
                f"{cpv_2_3s:,.0f} đ" if cpv_2_3s > 0 else "No data",  # CPV 2/3s
                f"{cpc:,.0f} đ" if cpc > 0 else "No data",  # CPC
                f"{cpe:,.0f} đ" if cpe > 0 else "No data"   # CPE
            ])
        
        # Calculate summary metrics for efficiency table
        if not efficiency_data:
            total_cpm = 0
            total_cpv = 0
            total_cpv_2_3s = 0
            total_cpc = 0
            total_cpe = 0
        else:
            # Calculate averages for cost metrics
            cpm_values = []
            cpv_values = []
            cpv_2_3s_values = []
            cpc_values = []
            cpe_values = []
            
            for row in efficiency_data:
                if row[8] and "đ" in str(row[8]):  # CPM column
                    try:
                        cpm_values.append(float(str(row[8]).replace(' đ', '').replace(',', '')))
                    except:
                        pass
                if row[9] and "đ" in str(row[9]):  # CPV column
                    try:
                        cpv_values.append(float(str(row[9]).replace(' đ', '').replace(',', '')))
                    except:
                        pass
                if row[10] and "đ" in str(row[10]):  # CPV 2/3s column
                    try:
                        cpv_2_3s_values.append(float(str(row[10]).replace(' đ', '').replace(',', '')))
                    except:
                        pass
                if row[11] and "đ" in str(row[11]):  # CPC column
                    try:
                        cpc_values.append(float(str(row[11]).replace(' đ', '').replace(',', '')))
                    except:
                        pass
                if row[12] and "đ" in str(row[12]):  # CPE column
                    try:
                        cpe_values.append(float(str(row[12]).replace(' đ', '').replace(',', '')))
                    except:
                        pass
            
            total_cpm = sum(cpm_values) / len(cpm_values) if cpm_values else 0
            total_cpv = sum(cpv_values) / len(cpv_values) if cpv_values else 0
            total_cpv_2_3s = sum(cpv_2_3s_values) / len(cpv_2_3s_values) if cpv_2_3s_values else 0
            total_cpc = sum(cpc_values) / len(cpc_values) if cpc_values else 0
            total_cpe = sum(cpe_values) / len(cpe_values) if cpe_values else 0
        
        # Add summary row
        efficiency_data.append([
            "TOTAL",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            f"{total_cpm:,.0f} đ" if total_cpm > 0 else "N/A",
            f"{total_cpv:,.0f} đ" if total_cpv > 0 else "N/A",
            f"{total_cpv_2_3s:,.0f} đ" if total_cpv_2_3s > 0 else "N/A",
            f"{total_cpc:,.0f} đ" if total_cpc > 0 else "N/A",
            f"{total_cpe:,.0f} đ" if total_cpe > 0 else "N/A"
        ])

        # Efficiency headers without separators
        efficiency_headers = [
            "Brand", "Funnel", "Platform", "Audience", "Region", "Format", 
            "Buying method", "KPI Metric", "CPM", "CPV", "CPV 2/3s", "CPC", "CPE"
        ]

        # Create third Material-UI Table
        with elements("efficiency_table"):
            with mui.Paper(
                elevation=0,
                sx={
                    "margin": "0",
                    "border": "1px solid #e2e8f0",
                    "overflow": "hidden",
                    "background": "#ffffff"
                }
            ):
                with mui.TableContainer(sx={"maxHeight": 600}):
                    with mui.Table(stickyHeader=True, size="small"):
                        # Table Header
                        with mui.TableHead():
                            with mui.TableRow():
                                for header in efficiency_headers:
                                    mui.TableCell(
                                        header,
                                        sx={
                                            "background": "#003366",
                                            "color": "white",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                            "fontSize": "0.75rem",
                                            "padding": "8px 6px",
                                            "borderBottom": "1px solid #e2e8f0",
                                            "borderRight": "1px solid #ffffff30"
                                        }
                                    )
                        
                        # Table Body
                        with mui.TableBody():
                            for i, row in enumerate(efficiency_data):
                                is_summary = i == len(efficiency_data) - 1
                                
                                with mui.TableRow(
                                    sx={
                                        "backgroundColor": "#f8f9fa" if is_summary else ("rgba(248, 249, 250, 0.5)" if i % 2 == 0 else "white"),
                                        "borderTop": "1px solid #dee2e6" if is_summary else "none",
                                        "&:hover": {
                                            "backgroundColor": "#f1f3f4" if not is_summary else "#e9ecef"
                                        }
                                    }
                                ):
                                    for j, cell in enumerate(row):
                                        # Color coding for cost efficiency metrics
                                        cell_color = "inherit"
                                        font_weight = "bold" if is_summary else "normal"
                                        
                                        # Color code cost metrics (lower is better)
                                        if j >= 8 and cell and "đ" in str(cell):  # Cost columns
                                            try:
                                                value = float(str(cell).replace(' đ', '').replace(',', ''))
                                                if value > 50000:
                                                    cell_color = "#dc3545"  # Red for high cost
                                                elif value > 20000:
                                                    cell_color = "#fd7e14"  # Orange for medium cost
                                                elif value > 0:
                                                    cell_color = "#28a745"  # Green for low cost
                                            except:
                                                pass
                                        
                                        mui.TableCell(
                                            str(cell),
                                            sx={
                                                "textAlign": "center",
                                                "padding": "6px 4px",
                                                "fontSize": "0.7rem",
                                                "color": cell_color if cell_color != "inherit" else "inherit",
                                                "fontWeight": font_weight,
                                                "borderBottom": "1px solid #e2e8f0",
                                                "borderRight": "1px solid #e2e8f0"
                                            }
                                        )
                        

