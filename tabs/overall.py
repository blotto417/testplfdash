import streamlit as st
import pandas as pd
from st_aggrid import JsCode, AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from streamlit_extras.stylable_container import stylable_container
import plotly.express as px
import plotly.graph_objects as go
from components import kpi_card, styled_metric_card_with_bar, styled_kpi_card, styled_kpi_card

def display(query_data, active_filters, min_date, max_date):
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
    # First, let's get the data grouped by dimensions
    dimension_columns = ["Funnel", "Brand", "Platform", "Region", "Format", "Audience", "Buying_Type", "Plan_Start_Date", "Plan_End_Date", "KPI_Metric "]
    metric_columns = [
        "net_media_cost", "Cost", "plan_active_day", "active_day", "KPI", "KPI_actual"
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
            margin-top: -4rem;
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
    COLUMN_HEIGHT_PX = 840  # Fixed height for both columns; adjust as necessary
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
                }}
            """
            ):
            st.markdown("### CAMPAIGN INFORMATION")
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(f"**{date_range}**")
            
            # Wrapper div for equal height cards
            st.markdown('<div style="display: flex; flex-direction: column; flex: 1; gap: 1rem;">', unsafe_allow_html=True)
            
            # Run Rate Card with enhanced visualization
            st.markdown('<div style="flex: 1; display: flex; flex-direction: column;">', unsafe_allow_html=True)
            
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
                value=f"{run_rate:.1f}",
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
                value=f"${spent:,.0f}",
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
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            padding: 1.25rem;
            height: {COLUMN_HEIGHT_PX}px;
            display: flex;
            flex-direction: column;
            gap: 1rem;
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
                    icon="👁️"
                )
            with key_col2:
                styled_kpi_card(
                    title="Engagements",
                    value=f"{safe_value(total_data['Engagements']):,.0f}",
                    icon="👍"
                )
            with key_col3:
                styled_kpi_card(
                    title="Clicks",
                    value=f"{safe_value(total_data['Clicks']):,.0f}",
                    icon="🖱️"
                )
            with key_col4:
                styled_kpi_card(
                    title="Views*",
                    value=f"{safe_value(total_data['Views']):,.0f}",
                    icon="📺"
                )
            st.markdown('</div>', unsafe_allow_html=True)
                
            # Row 2: TOTAL QUANTITY OF COMMITTED METRICS
            st.markdown('<div style="flex: 1;">', unsafe_allow_html=True)
            st.markdown("### TOTAL QUANTITY OF COMMITTED METRICS")
            comm_col1, comm_col2, comm_col3, comm_col4 = st.columns(4, gap="medium")
            
            with comm_col1:
                impression_percentage = (safe_value(total_data['Impression']) / safe_value(total_data['impression_plan']) * 100) if safe_value(total_data['impression_plan']) > 0 else 0
                styled_kpi_card(
                    title="Impression",
                    value=f"{safe_value(total_data['Impression']):,.0f}",
                    delta=f"{impression_percentage:.1f}% from committed",
                    icon="👁️"
                )
            with comm_col2:
                if safe_value(total_data['engagement_plan']) > 0:
                    engagement_percentage = (safe_value(total_data['Engagements']) / safe_value(total_data['engagement_plan']) * 100)
                    styled_kpi_card(
                        title="Engagements",
                        value=f"{safe_value(total_data['Engagements']):,.0f}",
                        delta=f"{engagement_percentage:.1f}% from committed",
                        icon="👍"
                    )
                else:
                    styled_kpi_card(
                        title="Engagements",
                        value="No data",
                        delta="No data from committed",
                        icon="👍"
                    )
            with comm_col3:
                if safe_value(total_data['click_plan']) > 0:
                    click_percentage = (safe_value(total_data['Clicks']) / safe_value(total_data['click_plan']) * 100)
                    styled_kpi_card(
                        title="Clicks",
                        value=f"{safe_value(total_data['Clicks']):,.0f}",
                        delta=f"{click_percentage:.1f}% from committed",
                        icon="🖱️"
                    )
                else:
                    styled_kpi_card(
                        title="Clicks",
                        value="No data",
                        delta="No data from committed",
                        icon="🖱️"
                    )
            with comm_col4:
                if safe_value(total_data['views_plan']) > 0:
                    views_percentage = (safe_value(total_data['Views']) / safe_value(total_data['views_plan']) * 100)
                    styled_kpi_card(
                        title="Views",
                        value=f"{safe_value(total_data['Views']):,.0f}",
                        delta=f"{views_percentage:.1f}% from committed",
                        icon="📺"
                    )
                else:
                    styled_kpi_card(
                        title="Views",
                        value="No data",
                        delta="No data from committed",
                        icon="📺"
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
                    icon="🌐"
                )
            with ga_col2:
                styled_kpi_card(
                    title="Add to Cart",
                    value=f"{safe_value(total_data['add_to_carts']):,.0f}",
                    icon="🛒"
                )
            with ga_col3:
                styled_kpi_card(
                    title="Purchase",
                    value=f"{safe_value(total_data['ecommerce_purchases']):,.0f}",
                    icon="🛍️"
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

    with stylable_container(
        key="vmk_detailed_data_container",
            css_styles=f"""
                {{
                    background: var(--card-bg);
                    border: 1px solid var(--gray-border);
                    border-radius: 8px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    padding: 1.25rem;
                }}
            """,
    ):
        st.markdown("### KPI COMPARISON BETWEEN PLAN AND ACTUAL")
        st.markdown(f"*Campaign period: {date_range}*")
        st.markdown("*Detailed breakdown of campaign performance metrics grouped by dimensions*")

        # --- Custom CSS for Modern Headers and Pinned Row ---
        custom_css = {
            ".ag-header-cell-label": {
                "font-size": "14px",
                "font-weight": "600",
                "color": "#FFFFFF",
                "white-space": "normal",
                "word-wrap": "break-word",
                "line-height": "1.2",
                "height": "auto",
                "min-height": "40px",
                "display": "flex",
                "align-items": "center",
                "justify-content": "center",
                "text-align": "center"
            },
            ".ag-header-cell": {
                "height": "auto",
                "min-height": "40px",
                "display": "flex",
                "align-items": "center",
                "border-right": "1px solid #0066CC"
            },
            ".ag-header-cell:last-child": {
                "border-right": "none"
            },
            ".ag-header": {
                "background-color": "#003366",
                "border-bottom": "2px solid #0066CC"
            },
            ".ag-row-hover": {
                "background-color": "#E6F3FF !important"
            },
            ".ag-row-pinned": {
                "font-weight": "bold",
                "background-color": "#dbeafe !important",
                "border-top": "2px solid #3b82f6 !important"
            }
        }
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(
            resizable=True,
            filterable=True,
            sortable=True,
            editable=False,
        )

        # --- Conditional Formatting and Data Bars ---
        
        # Data bar for KPI
        max_kpi = df['KPI'].max()
        kpi_renderer = JsCode(f"""
            class KpiRenderer {{
                init(params) {{
                    this.eGui = document.createElement('div');
                    this.eGui.style.position = 'relative';
                    this.eGui.style.height = '100%';
                    this.eGui.style.width = '100%';

                    let value = params.value;
                    let percentage = (value / {max_kpi}) * 100;
                    
                    let bar = document.createElement('div');
                    bar.style.backgroundColor = 'rgba(40, 167, 69, 0.3)';
                    bar.style.height = '100%';
                    bar.style.width = percentage + '%';
                    
                    let text = document.createElement('span');
                    text.style.position = 'absolute';
                    text.style.left = '8px';
                    text.style.top = '50%';
                    text.style.transform = 'translateY(-50%)';
                    text.innerText = value.toLocaleString('en-US');

                    this.eGui.appendChild(bar);
                    this.eGui.appendChild(text);
                }}
                getGui() {{
                    return this.eGui;
                }}
            }}
        """)
        
        # Data bar for KPI Actual
        max_kpi_actual = df['KPI_actual'].max()
        kpi_actual_renderer = JsCode(f"""
            class KpiActualRenderer {{
                init(params) {{
                    this.eGui = document.createElement('div');
                    this.eGui.style.position = 'relative';
                    this.eGui.style.height = '100%';
                    this.eGui.style.width = '100%';

                    let value = params.value;
                    let percentage = (value / {max_kpi_actual}) * 100;
                    
                    let bar = document.createElement('div');
                    bar.style.backgroundColor = 'rgba(0, 123, 255, 0.3)';
                    bar.style.height = '100%';
                    bar.style.width = percentage + '%';
                    
                    let text = document.createElement('span');
                    text.style.position = 'absolute';
                    text.style.left = '8px';
                    text.style.top = '50%';
                    text.style.transform = 'translateY(-50%)';
                    text.innerText = value.toLocaleString('en-US');

                    this.eGui.appendChild(bar);
                    this.eGui.appendChild(text);
                }}
                getGui() {{
                    return this.eGui;
                }}
            }}
        """)
        
        # Enhanced percentage formatting
        percentage_formatter = JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return '';
                }
                return (params.value * 100).toFixed(2) + '%';
            }
        """)
        
        # Currency formatter
        currency_formatter = JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return '';
                }
                return '₫' + params.value.toLocaleString('en-US');
            }
        """)
        
        # Number formatter with commas
        number_formatter = JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return '';
                }
                return params.value.toLocaleString('en-US');
            }
        """)
        
        # Conditional styling for spent percentage (highlight over 100%)
        spent_percentage_style = JsCode("""
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
                        'color': '#FFA500',
                        'fontWeight': '600'
                    };
                }
                return { 'color': '#28A745' };
            }
        """)
        
        # Conditional styling for KPI percentage
        kpi_percentage_style = JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return { 'color': 'black' };
                }
                if (params.value >= 100) {
                    return {
                        'color': '#28A745',
                        'fontWeight': '600'
                    };
                } else if (params.value >= 80) {
                    return {
                        'color': '#FFA500',
                        'fontWeight': '600'
                    };
                }
                return { 'color': '#DC3545' };
            }
        """)

        # Configure all columns with proper formatting
        gb.configure_column("Funnel", headerName="Funnel", width=80)
        gb.configure_column("Brand", headerName="Brand", width=80)
        gb.configure_column("Platform", headerName="Platform", width=120)
        gb.configure_column("Region", headerName="Region", width=100)
        gb.configure_column("Format", headerName="Format", width=150)
        gb.configure_column("Audience", headerName="Audience", width=80)
        gb.configure_column("Buying_Type", headerName="Buying Type", width=80)
        gb.configure_column("Plan_Start_Date", headerName="Start Date", width=80)
        gb.configure_column("Plan_End_Date", headerName="End Date", width=80)
        gb.configure_column("KPI_Metric", headerName="KPI Metric", width=80)

        # Financial metrics
        gb.configure_column("net_media_cost", headerName="Plan Cost", width=120, valueFormatter=currency_formatter)
        gb.configure_column("Cost", headerName="Spent", width=120, valueFormatter=currency_formatter)
        gb.configure_column("Spent_Percentage", headerName="%Spent", width=100, valueFormatter=percentage_formatter, cellStyle=spent_percentage_style)
        
        # Time metrics
        gb.configure_column("plan_active_day", headerName="Plan Days", width=100, valueFormatter=number_formatter)
        gb.configure_column("active_day", headerName="Active Days", width=100, valueFormatter=number_formatter)
        gb.configure_column("Run_Rate", headerName="Run Rate", width=100, valueFormatter=percentage_formatter)
        
        # Performance metrics
        gb.configure_column("KPI", headerName="KPI (Plan)", width=120, cellRenderer=kpi_renderer)
        gb.configure_column("KPI_actual", headerName="KPI Actual", width=120, cellRenderer=kpi_actual_renderer)
        gb.configure_column("KPI_Actual_Percentage", headerName="%KPI Actual", width=120, valueFormatter=percentage_formatter, cellStyle=kpi_percentage_style)
        
        # Efficiency metrics
        gb.configure_column("Cost_Per_Unit", headerName="Cost/Unit", width=120, valueFormatter=currency_formatter)
        
        # Progress metric
        gb.configure_column("Progress", headerName="Progress", width=120, valueFormatter=JsCode("""
            function(params) {
                if (params.value === null || typeof params.value === 'undefined') {
                    return '';
                }
                return params.value.toFixed(2) + ' pts';
            }
        """))

        gridOptions = gb.build()

        # --- Create and add the summary row ---
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
                "Funnel": "",
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

        AgGrid(
            df,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            theme='ag-theme-quartz',
            custom_css=custom_css,
            height=600,
            width='100%',
            reload_data=True,
            fit_columns_on_grid_load=False,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW
        )
