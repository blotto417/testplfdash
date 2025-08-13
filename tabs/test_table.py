import streamlit as st
import pandas as pd
from st_aggrid import JsCode, AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from streamlit_extras.stylable_container import stylable_container
import plotly.express as px
import plotly.graph_objects as go
from components import kpi_card, styled_metric_card_with_bar, styled_kpi_card
from tabs.formatters import currency_formatter, percentage_formatter, number_formatter, center_header_css

def display(query_data, active_filters, min_date, max_date):
    """
    Display a beautiful test table with summary columns and enhanced styling using actual SQL data
    """
    
    # Query summary data from the first table
    summary_columns = [
        "net_media_cost", "Cost", "plan_active_day", "active_day", "Impression", 
        "Engagements", "Clicks", "Views", "impression_plan", "engagement_plan", 
        "click_plan", "views_plan", "sessions", "add_to_carts", "ecommerce_purchases",
        "Plan_Start_Date", "Plan_End_Date"
    ]

    summary_df = query_data(
        columns=summary_columns,
        tablename="report_campaign_overall_total_notcs",
        filters=active_filters,
        start_date=min_date,
        end_date=max_date,
        aggregations={
            "net_media_cost": "AVG", "plan_active_day": "AVG", "impression_plan": "AVG",
            "engagement_plan": "AVG", "click_plan": "AVG", "views_plan": "AVG",
            "Cost": "SUM", "active_day": "SUM", "Impression": "SUM", "Engagements": "SUM",
            "Clicks": "SUM", "Views": "SUM", "sessions": "SUM", "add_to_carts": "SUM",
            "ecommerce_purchases": "SUM",
            "Plan_Start_Date": "MIN", "Plan_End_Date": "MAX"
        },
        group_by=[]
    )
    
    if summary_df.empty:
        st.warning("No data available for the selected filters.")
        return
        
    # Query detailed data for the AgGrid table with enhanced dimensions and metrics
    dimension_columns = ["Funnel", "Brand", "Platform", "Region", "Format", "Audience", "Buying_Type", "Plan_Start_Date", "Plan_End_Date", "KPI_Metric "]
    metric_columns = [
        "net_media_cost", "Cost", "plan_active_day", "active_day", "KPI", "KPI_actual"
    ]
   
    # Get aggregated data grouped by dimensions
    df = query_data(
        columns=dimension_columns + metric_columns,
        tablename="report_campaign_overall_total",
        filters=active_filters,
        start_date=min_date,
        end_date=max_date,
        aggregations={
            "net_media_cost": "AVG", "Cost": "AVG", "plan_active_day": "AVG", 
            "active_day": "AVG", "KPI": "AVG", "KPI_actual": "AVG"
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
                lambda row: (row["KPI_actual"] / row["KPI"] * 100) if row.get("KPI") and row["KPI"] > 0 else 0,
                axis=1
            )
            
            # Cost per unit calculation (cost per impression)
            df["Cost_Per_Unit"] = df.apply(
                lambda row: (row["Cost"] / row["KPI_actual"]) if row.get("KPI_actual") and row["KPI_actual"] > 0 else 0,
                axis=1
            )
            
            # Add date range from summary data
            plan_start = summary_df.iloc[0].get('Plan_Start_Date', min_date)
            plan_end = summary_df.iloc[0].get('Plan_End_Date', max_date)
            
            # Convert plan_start and plan_end to datetime objects if they are strings
            if isinstance(plan_start, str):
                plan_start = pd.to_datetime(plan_start)
            if isinstance(plan_end, str):
                plan_end = pd.to_datetime(plan_end)
                
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
    
        # Create beautiful header
    with stylable_container(
        key="test_table_header",
        css_styles="""
            {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem 1.5rem;
                border-radius: 12px;
                margin-bottom: 2rem;
                margin-top: -5rem;

                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.2);
            }
        """
    ):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Calculate campaign information from summary data
            total_data = summary_df.iloc[0]  # Get the aggregated row
            
            # Helper function to safely handle None values
            def safe_value(val, default=0):
                return val if val is not None else default
            
            # Calculate run rate
            run_rate = (total_data['active_day'] / total_data['plan_active_day']) if total_data['plan_active_day'] is not None and total_data['plan_active_day'] > 0 else 0
            run_rate_percentage = (run_rate - 1) * 100  # Convert to percentage from plan
            
            # Format date range
            plan_start = total_data.get('Plan_Start_Date', min_date)
            plan_end = total_data.get('Plan_End_Date', max_date)
            
            # Convert plan_start and plan_end to datetime objects if they are strings
            if isinstance(plan_start, str):
                plan_start = pd.to_datetime(plan_start)
            if isinstance(plan_end, str):
                plan_end = pd.to_datetime(plan_end)
                
            if plan_start and plan_end:
                start_date = plan_start.strftime('%b %d, %Y')
                end_date = plan_end.strftime('%b %d, %Y')
                total_days = (plan_end - plan_start).days
            else:
                start_date = min_date.strftime('%b %d, %Y')
                end_date = max_date.strftime('%b %d, %Y')
                total_days = (max_date - min_date).days
                
            active_days = safe_value(total_data['active_day'])
            run_rate_display = run_rate * 100  # Convert to percentage for display
            
            st.markdown(
                f"""
                <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    📊 SN-FM100-FM100PromoAprMay-2403-3105
                </h1>
                <div style="display: flex; align-items: center; gap: 2rem; margin-top: 1rem;">
                    <div style="display: flex; align-items: center; background: rgba(255,255,255,0.15); padding: 0.75rem 1rem; border-radius: 8px; backdrop-filter: blur(10px);">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">📅</span>
                        <div>
                            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.8); margin-bottom: 0.2rem;">Campaign Period</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: white;">{start_date} → {end_date}</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; background: rgba(255,255,255,0.15); padding: 0.75rem 1rem; border-radius: 8px; backdrop-filter: blur(10px);">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">🏃‍♂️</span>
                        <div>
                            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.8); margin-bottom: 0.2rem;">Run Rate</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: white;">
                                {run_rate_display:.1f}% 
                                <span style="font-size: 0.9rem; color: rgba(255,255,255,0.8);">({active_days}/{total_days} days)</span>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; background: rgba(255,255,255,0.15); padding: 0.75rem 1rem; border-radius: 8px; backdrop-filter: blur(10px);">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">⏱️</span>
                        <div>
                            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.8); margin-bottom: 0.2rem;">Duration</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: white;">{total_days} days</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            # Calculate budget allocation from summary data
            total_spent = safe_value(total_data['Cost'])
            total_budget = safe_value(total_data['net_media_cost'])
            budget_allocation = (total_spent / total_budget * 100) if total_budget > 0 else 0
            
            styled_kpi_card(
                title="Budget Allocation",
                value=f"{total_spent:,.0f}",
                delta=f"{budget_allocation:.1f}% of {total_budget:,.0f}",
                icon="💰",
                progress_value=float(budget_allocation),
                progress_max=100.0,
                color="blue"
            )
        
        with col3:
            # Calculate progress (budget vs run rate)
            progress_diff = run_rate - (total_spent / total_budget) if total_budget > 0 else 0
            
            styled_kpi_card(
                title="Progress",
                value=f"{progress_diff:+.1f}pts",
                delta="Run Rate vs Budget",
                icon="📈",
                progress_value=float(abs(progress_diff)),
                progress_max=50.0,
                color="green" if progress_diff >= 0 else "red"
            )
    
    # Summary metrics row with enhanced committed card style
    with stylable_container(
        key="test_table_summary",
        css_styles="""
            {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid #e1e5e9;
            }
        """
    ):
        st.markdown("### 📈 Commited KPIs Summary")
        
        # Add CSS for progress bars
        st.markdown("""
        <style>
            .progress-bar-container {
                width: 100%;
                background-color: #e5e7eb;
                border-radius: 4px;
                height: 10px;
                overflow: hidden;
            }
            .progress-bar {
                height: 10px;
                border-radius: 4px;
                transition: width 0.3s ease-in-out;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Calculate summary metrics from summary data for KPI metrics
        impressions_actual = safe_value(total_data.get('Impression', 0))
        impressions_plan = safe_value(total_data.get('impression_plan', 0))
        
        clicks_actual = safe_value(total_data.get('Clicks', 0))
        clicks_plan = safe_value(total_data.get('click_plan', 0))
        
        engagements_actual = safe_value(total_data.get('Engagements', 0))
        engagements_plan = safe_value(total_data.get('engagement_plan', 0))
        
        views_actual = safe_value(total_data.get('Views', 0))
        views_plan = safe_value(total_data.get('views_plan', 0))
        
        # Calculate average utilization for insights section
        avg_utilization = float(df['Spent_Percentage'].mean()) if not df.empty else 0
        
        # Create metrics data for enhanced cards - KPI focused
        metrics_data = [
            {
                "name": "Impressions",
                "total_actual": impressions_actual,
                "committed": impressions_plan * 0.8,  # 80% of plan as committed target
                "total_with_committed": impressions_plan,  # Full plan as total with committed
                "icon": "👁️",
                "color": "#3B82F6"
            },
            {
                "name": "Clicks",
                "total_actual": clicks_actual,
                "committed": clicks_plan * 0.8,  # 80% of plan as committed target
                "total_with_committed": clicks_plan,  # Full plan as total with committed
                "icon": "👆",
                "color": "#10B981"
            },
            {
                "name": "Engagements",
                "total_actual": engagements_actual,
                "committed": engagements_plan * 0.8,  # 80% of plan as committed target
                "total_with_committed": engagements_plan,  # Full plan as total with committed
                "icon": "💬",
                "color": "#F59E0B"
            },
            {
                "name": "Views",
                "total_actual": views_actual,
                "committed": views_plan * 0.8,  # 80% of plan as committed target
                "total_with_committed": views_plan,  # Full plan as total with committed
                "icon": "📺",
                "color": "#8B5CF6"
            }
        ]
        
        # GA4 metrics data (simple cards without progress bars)
        ga4_metrics = [
            {
                "name": "Sessions",
                "value": 125000,
                "icon": "🌐",
                "color": "#6366F1"
            },
            {
                "name": "Add to Cart",
                "value": 8500,
                "icon": "🛒",
                "color": "#EC4899"
            },
            {
                "name": "Purchases",
                "value": 3200,
                "icon": "🛍️",
                "color": "#10B981"
            },
            {
                "name": "Revenue",
                "value": 450000,
                "icon": "💵",
                "color": "#F59E0B"
            }
        ]
        
        # Display metrics in a single row with four columns
        cols = st.columns(4)
        for i, metric in enumerate(metrics_data):
            with cols[i]:
                display_enhanced_metric_card(metric)
    
    # GA4 Metrics section
    with stylable_container(
        key="test_table_ga4",
        css_styles="""
            {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid #e1e5e9;
            }
        """
    ):
        st.markdown("### 📊 GA4 Metrics")
        
        # Display GA4 metrics in a single row with four columns
        ga4_cols = st.columns(4)
        for i, metric in enumerate(ga4_metrics):
            with ga4_cols[i]:
                display_simple_metric_card(metric)
    
    # Main table container
    with stylable_container(
        key="test_table_container",
        css_styles="""
            {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid #e1e5e9;
            }
        """
    ):
        st.markdown("### 🎯 Detailed Actual vs Committed")
        st.markdown("*Text*")
        
        # Custom CSS for beautiful table styling
        custom_css = {
            ".ag-header-cell-label": {
                "font-size": "10px",
                "font-weight": "600",
                "color": "#FFFFFF",
                "white-space": "normal",
                "word-wrap": "break-word",
                "line-height": "1.2",
                "height": "100%",
                "width": "100%",
                "display": "flex",
                "align-items": "center",
                "justify-content": "center",
                "text-align": "center",
                "padding": "6px 3px",
                "overflow": "visible",
                "vertical-align": "middle"
            },
            ".ag-header-cell": {
                "height": "auto",
                "min-height": "40px",
                "max-height": "none",
                "display": "flex",
                "align-items": "center",
                "justify-content": "center",
                "border-right": "1px solid #4A90E2",
                "overflow": "visible",
                "vertical-align": "middle"
            },
            ".ag-header-cell:last-child": {
                "border-right": "none"
            },
            ".ag-header": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "border-bottom": "2px solid #4A90E2",
                "height": "auto",
                "min-height": "40px",
                "max-height": "none",
                "display": "flex",
                "align-items": "center"
            },
            ".ag-header-row": {
                "height": "auto",
                "min-height": "40px",
                "max-height": "none",
                "display": "flex",
                "align-items": "center"
            },
            ".ag-row-hover": {
                "background-color": "#F8F9FF !important",
                "transition": "background-color 0.2s ease"
            },
            ".ag-row-pinned": {
                "font-weight": "bold",
                "background-color": "#E3F2FD !important",
                "border-top": "2px solid #2196F3 !important",
                "color": "#1976D2"
            },
            ".ag-row": {
                "border-bottom": "1px solid #E0E0E0",
                "font-size": "11px"
            },
            ".ag-row:nth-child(even)": {
                "background-color": "#FAFAFA"
            },
            ".ag-cell": {
                "font-size": "11px",
                "padding": "4px 6px"
            }
        }
        
        # Configure grid options
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(
            resizable=True,
            filterable=True,
            sortable=True,
            editable=False,
        )
        
        # Add grid options for better horizontal scrolling
        gb.configure_grid_options(
            suppressHorizontalScroll=False,  # Enable horizontal scrolling
            alwaysShowHorizontalScroll=True,  # Always show horizontal scrollbar
            suppressColumnVirtualisation=False,  # Enable column virtualization for performance
            enableRangeSelection=True,  # Enable range selection
            suppressRowClickSelection=True,  # Prevent row selection on click
        )
        
        # Add center alignment CSS
        st.markdown(f"""
        <style>
            {center_header_css}
        </style>
        """, unsafe_allow_html=True)
        
        # Conditional styling for budget utilization
        utilization_style = JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return { 'color': 'black' };
                }
                if (params.value > 100) {
                    return {
                        'color': '#DC3545',
                        'fontWeight': '600',
                        'backgroundColor': '#ffe6e6'
                    };
                } else if (params.value > 80) {
                    return {
                        'color': '#28A745',
                        'fontWeight': '600',
                        'backgroundColor': '#e8f5e8'
                    };
                } else if (params.value > 50) {
                    return {
                        'color': '#FFA500',
                        'fontWeight': '600'
                    };
                }
                return { 'color': '#6C757D' };
            }
        """)
        
        # Status styling
        status_style = JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return { 'color': 'black' };
                }
                if (params.value === 'Active') {
                    return {
                        'color': '#28A745',
                        'fontWeight': '600',
                        'backgroundColor': '#e8f5e8',
                        'borderRadius': '12px',
                        'padding': '4px 8px',
                        'textAlign': 'center'
                    };
                } else if (params.value === 'Paused') {
                    return {
                        'color': '#FFA500',
                        'fontWeight': '600',
                        'backgroundColor': '#fff3cd',
                        'borderRadius': '12px',
                        'padding': '4px 8px',
                        'textAlign': 'center'
                    };
                } else if (params.value === 'Completed') {
                    return {
                        'color': '#6C757D',
                        'fontWeight': '600',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '12px',
                        'padding': '4px 8px',
                        'textAlign': 'center'
                    };
                }
                return { 'color': 'black' };
            }
        """)

        # Configure columns with proper formatting - mapped to actual data structure
        gb.configure_column("Funnel", headerName="Funnel", width=100, minWidth=80, cellStyle={'textAlign': 'center'})
        gb.configure_column("Brand", headerName="Brand", width=120, minWidth=100, cellStyle={'textAlign': 'center'})
        gb.configure_column("Platform", headerName="Platform", width=120, minWidth=100, cellStyle={'textAlign': 'center'})
        gb.configure_column("Region", headerName="Region", width=100, minWidth=80, cellStyle={'textAlign': 'center'})
        gb.configure_column("Format", headerName="Format", width=140, minWidth=120, cellStyle={'textAlign': 'center'})
        gb.configure_column("Audience", headerName="Audience", width=120, minWidth=100, cellStyle={'textAlign': 'center'})
        gb.configure_column("Buying_Type", headerName="Buying Type", width=120, minWidth=100, cellStyle={'textAlign': 'center'})
        gb.configure_column("Plan_Start_Date", headerName="Start Date", width=120, minWidth=100, cellStyle={'textAlign': 'center'})
        gb.configure_column("Plan_End_Date", headerName="End Date", width=120, minWidth=100, cellStyle={'textAlign': 'center'})
        gb.configure_column("KPI_Metric", headerName="KPI Metric", width=120, minWidth=100, cellStyle={'textAlign': 'center'})

        # Financial metrics
        gb.configure_column("net_media_cost", headerName="Plan Cost", width=120, minWidth=100, valueFormatter=currency_formatter, cellStyle={'textAlign': 'center'})
        gb.configure_column("Cost", headerName="Spent", width=120, minWidth=100, valueFormatter=currency_formatter, cellStyle={'textAlign': 'center'})
        gb.configure_column("Spent_Percentage", headerName="%Spent", width=100, minWidth=80, valueFormatter=percentage_formatter, cellStyle=utilization_style)
        
        # Time metrics
        gb.configure_column("plan_active_day", headerName="Plan Days", width=100, minWidth=80, valueFormatter=number_formatter, cellStyle={'textAlign': 'center'})
        gb.configure_column("active_day", headerName="Active Days", width=120, minWidth=100, valueFormatter=number_formatter, cellStyle={'textAlign': 'center'})
        gb.configure_column("Run_Rate", headerName="Run Rate", width=100, minWidth=80, valueFormatter=percentage_formatter, cellStyle={'textAlign': 'center'})
        
        # Performance metrics
        gb.configure_column("KPI", headerName="KPI (Plan)", width=120, minWidth=100, valueFormatter=number_formatter, cellStyle={'textAlign': 'center'})
        gb.configure_column("KPI_actual", headerName="KPI Actual", width=120, minWidth=100, valueFormatter=number_formatter, cellStyle={'textAlign': 'center'})
        gb.configure_column("KPI_Actual_Percentage", headerName="%KPI Actual", width=120, minWidth=100, valueFormatter=percentage_formatter, cellStyle={'textAlign': 'center'})
        
        # Efficiency metrics
        gb.configure_column("Cost_Per_Unit", headerName="Cost/Unit", width=120, minWidth=100, valueFormatter=currency_formatter, cellStyle={'textAlign': 'center'})
        
        # Progress metric
        gb.configure_column("Progress", headerName="Progress", width=100, minWidth=80, valueFormatter=JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return '';
                }
                return params.value.toFixed(2) + ' pts';
            }
        """), cellStyle={'textAlign': 'center'})
        
        gridOptions = gb.build()
        
        # Add summary row
        if not df.empty:
            # Calculate totals for key metrics
            cost_sum = df['Cost'].sum()
            net_media_cost_avg = df['net_media_cost'].mean()  # Use average for plan data
            kpi_sum = df['KPI'].sum()
            kpi_actual_sum = df['KPI_actual'].sum()
            
            # Calculate summary metrics
            total_spent_percentage = (cost_sum / net_media_cost_avg * 100) if net_media_cost_avg > 0 else 0
            total_kpi_percentage = (kpi_actual_sum / kpi_sum * 100) if kpi_sum > 0 else 0
            total_cost_per_unit = (cost_sum / kpi_actual_sum) if kpi_actual_sum > 0 else 0
            
            summary_row = {
                "Funnel": "TOTAL",
                "Brand": "",
                "Platform": "",
                "Region": "",
                "Format": "",
                "Audience": "",
                "Buying_Type": "",
                "Plan_Start_Date": "",
                "Plan_End_Date": "",
                "KPI_Metric": "",
                "net_media_cost": net_media_cost_avg,
                "Cost": cost_sum,
                "Spent_Percentage": total_spent_percentage,
                "plan_active_day": "",
                "active_day": "",
                "Run_Rate": "",
                "KPI": kpi_sum,
                "KPI_actual": kpi_actual_sum,
                "KPI_Actual_Percentage": total_kpi_percentage,
                "Cost_Per_Unit": total_cost_per_unit,
                "Progress": ""
            }
            
            gridOptions['pinnedBottomRowData'] = [summary_row]
        
        # Display the table
        AgGrid(
            df,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            theme='ag-theme-quartz',
            custom_css=custom_css,
            height=500,
            width='100%',
            reload_data=False,  # Changed: Prevent data reloading on scroll
            fit_columns_on_grid_load=False,
            columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE  # Changed: Allow natural column sizing
        )
    
    # Additional insights section
    with stylable_container(
        key="test_table_insights",
        css_styles="""
            {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                border-radius: 12px;
                padding: 1.5rem;
                margin-top: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }
        """
    ):
        st.markdown(
            """
            <h3 style="color: white; margin: 0 0 1rem 0;">💡 Key Insights</h3>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Best performing campaign
            if not df.empty:
                best_campaign = df.loc[df['KPI_Actual_Percentage'].idxmax()]
                st.markdown(
                    f"""
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <h4 style="color: white; margin: 0 0 0.5rem 0;">🏆 Best Performer</h4>
                        <p style="color: rgba(255,255,255,0.9); margin: 0;">
                            <strong>{best_campaign['Brand']}</strong> on {best_campaign['Platform']}<br>
                            KPI Achievement: {best_campaign['KPI_Actual_Percentage']:.1f}%
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <h4 style="color: white; margin: 0 0 0.5rem 0;">🏆 Best Performer</h4>
                        <p style="color: rgba(255,255,255,0.9); margin: 0;">
                            No data available
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        with col2:
            # Budget utilization insights
            high_utilization = df[df['Spent_Percentage'] > 80]
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h4 style="color: white; margin: 0 0 0.5rem 0;">💰 Budget Efficiency</h4>
                    <p style="color: rgba(255,255,255,0.9); margin: 0;">
                        {len(high_utilization)} campaigns with >80% budget utilization<br>
                        Average utilization: {avg_utilization:.1f}%
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

def display_enhanced_metric_card(metric):
    """Display a self-contained metric card using a single HTML block."""
    
    # Calculate progress: Total (with committed) / Committed
    progress_pct = (metric['total_with_committed'] / metric['committed'] * 100) if metric['committed'] > 0 else 0
    progress_width = min(progress_pct, 100)
    
    progress_color = "green" if progress_pct >= 100 else "orange" if progress_pct >= 80 else "red"
    
    metric_class = f"metric-card metric-card-{metric['name'].lower().replace(' ', '-')}"

    card_html = f"""
        <div class="{metric_class}" style="background: linear-gradient(to right, {metric['color']}25, {metric['color']}10, #ffffff); padding: 12px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 5px solid {metric['color']};">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 24px; text-align: center; padding-right: 10px;">{metric['icon']}</div>
                <h3 style="margin: 0; color: #1f2937; font-weight: 600; flex-grow: 1;">{metric['name']}</h3>
            </div>
            <hr style="margin: 10px 0; border-color: #e5e7eb;">
            <div style="display: flex; justify-content: space-between;">
                <div style="text-align: left;">
                    <p style="font-size: 11px; color: #6b7280; margin: 0;">Total (Actual)</p>
                    <p style="font-size: 22px; font-weight: 700; color: {metric['color']}; margin: 0;">{metric['total_actual']:,.0f}</p>
                </div>
                <div style="text-align: right;">
                    <p style="font-size: 11px; color: #6b7280; margin: 0;">Committed</p>
                    <p style="font-size: 22px; font-weight: 700; color: #1f2937; margin: 0;">{metric['committed']:,.0f}</p>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <p style="font-size: 10px; color: #6b7280; margin: 0;">Progress vs. Committed</p>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {progress_width}%; background-color: {progress_color};"></div>
                </div>
                <p style="font-size: 12px; font-weight: 600; color: {progress_color}; text-align: right; margin-top: -2px;">{progress_pct:.1f}% of {metric['total_with_committed']:,.0f}</p>
            </div>
        </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def get_status_indicator(percentage):
    """Get status indicator based on percentage"""
    if percentage >= 100:
        return "✅ Exceeding"
    elif percentage >= 80:
        return "⚠️ On Track"
    else:
        return "❌ Behind"


def display_simple_metric_card(metric):
    """Display a simple metric card without progress bars."""
    
    # Format value based on metric type
    formatted_value = f"{metric['value']:,.0f}"
    
    card_html = f"""
        <div style="background: white; padding: 12px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-left: 4px solid {metric['color']};">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="font-size: 24px; text-align: center; padding-right: 10px;">{metric['icon']}</div>
                <h3 style="margin: 0; color: #1f2937; font-weight: 600; flex-grow: 1;">{metric['name']}</h3>
            </div>
            <div style="text-align: center;">
                <p style="font-size: 24px; font-weight: 700; color: {metric['color']}; margin: 0;">{formatted_value}</p>
            </div>
        </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
