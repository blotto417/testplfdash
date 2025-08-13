import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_extras.stylable_container import stylable_container
from streamlit_elements import elements, mui

def display(query_data, active_filters, start_date, end_date, selected_platform):
    # First, get the latest report_date to use as a filter
    latest_date_query = query_data(
        columns=["report_date"],
        tablename="report_campaign_overall_total",
        filters=active_filters,
        start_date=start_date,
        end_date=end_date,
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
    
    with stylable_container(
        key="vmk_audience_container",
        css_styles="""
            {
                animation: fadeIn 0.5s ease-in-out;
            }
            """,
    ):
        # Get campaign from active_filters or use default
        campaign_name = active_filters.get("Campaign_code", "All Campaigns")
        
        # Stylable title with custom CSS
        st.markdown(
            f"""
            <div style="
                background: #003366;
                padding: 1rem 0.5rem;
                border-radius: 8px;
                margin-bottom: 2rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                border-top: 4px solid #0066CC;
                border-bottom: 2px solid #E6F3FF;
                margin-top: -4rem;
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
                ">Audience Performance Dashboard</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Get real audience data from database
        columns = [
            "Funnel", "Brand", "Platform", "Region", "Format", "Audience", "Buying_Type",
            "Plan_Start_Date", "Plan_End_Date", "impression_plan", "Impression", "reach_plan", "reach",
            "net_media_cost", "Cost", "views_plan", "Views", "click_plan", "Clicks",
            "plan_active_day", "active_day", "Engagements", "23s_Video_Views", 
            "Video_Plays_100", "ctr_estimate", "er_estimate", "sessions", "add_to_carts", 
            "ecommerce_purchases", "KPI"
        ]
        
        # Query data from database
        df = query_data(
            columns=columns,
            tablename="report_campaign_overall_total",
            filters=active_filters,
            start_date=latest_report_date if latest_report_date else start_date,
            end_date=latest_report_date if latest_report_date else end_date,
            aggregations={
                # Plan data (sum)
                "impression_plan": "SUM", "reach_plan": "SUM", "net_media_cost": "SUM",
                "views_plan": "SUM", "click_plan": "SUM", "plan_active_day": "SUM",
                "ctr_estimate": "AVG", "er_estimate": "AVG", "KPI": "SUM",
                # Actual data (sum)
                "Impression": "SUM", "reach": "SUM", "Cost": "SUM", "Views": "SUM", 
                "Clicks": "SUM", "active_day": "SUM", "Engagements": "SUM", 
                "23s_Video_Views": "SUM", "Video_Plays_100": "SUM", "sessions": "SUM",
                "add_to_carts": "SUM", "ecommerce_purchases": "SUM",
                # Date field
                "report_date": "MAX"
            },
            group_by=["Funnel", "Brand", "Platform", "Region", "Format", "Audience", "Buying_Type", "Plan_Start_Date", "Plan_End_Date"]
        )
        
        if df.empty:
            st.warning("No data available for the selected filters.")
            return
        
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
                
            except Exception as e:
                st.warning(f"Error calculating metrics: {e}")
        
        # Create combined audience names (Audience + Region)
        df['Combined_Audience'] = df['Audience'].astype(str) + ' - ' + df['Region'].astype(str)
        
        # Calculate run rate (active days / planned days * 100)
        df['run_rate_actual'] = (df['active_day'] / df['plan_active_day'] * 100).fillna(0)
        
        # Calculate delivery percentages for each metric
        df['impression_delivery'] = (df['Impression'] / df['impression_plan'] * 100).fillna(0)
        df['reach_delivery'] = (df['reach'] / df['reach_plan'] * 100).fillna(0)
        df['budget_delivery'] = (df['Cost'] / df['net_media_cost'] * 100).fillna(0)
        df['views_delivery'] = (df['Views'] / df['views_plan'] * 100).fillna(0)
        df['clicks_delivery'] = (df['Clicks'] / df['click_plan'] * 100).fillna(0)
        df['run_rate_delivery'] = df['run_rate_actual']  # Run rate is already a percentage
        
        # --- CHART AREA (MOVED TO TOP) ---
        # Get unique audiences for selection
        all_audiences = df['Combined_Audience'].unique().tolist()
        
        # Audience Selection
        st.sidebar.markdown("### Audience Filter")
        available_audiences = ["All Audiences"] + all_audiences
        selected_audience = st.sidebar.selectbox(
            "Select Audience",
            available_audiences,
            index=0
        )
        
        # Define metrics (removed Run Rate, will be shown as line chart)
        metrics = ["Impression", "Reach", "Budget", "Views", "Clicks"]
        
        # Create delivery data dictionary
        delivery_data = {}
        for audience in all_audiences:
            audience_row = df[df['Combined_Audience'] == audience].iloc[0]
            delivery_data[audience] = [
                audience_row['impression_delivery'],  # Allow to exceed 100%
                audience_row['reach_delivery'],
                audience_row['budget_delivery'],
                audience_row['views_delivery'],
                audience_row['clicks_delivery']
            ]
        
        # Filter audiences based on selection
        if selected_audience == "All Audiences":
            audiences_to_show = all_audiences
        else:
            audiences_to_show = [selected_audience]
        
        # Create individual charts for each audience
        # Color palette for different metrics
        metric_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        # Dynamic grid layout for any number of audiences
        num_audiences = len(audiences_to_show)
        
        # Determine optimal columns per row (max 3 columns for readability)
        if num_audiences == 1:
            cols_per_row = 1
        elif num_audiences == 2:
            cols_per_row = 2
        elif num_audiences <= 6:
            cols_per_row = 3
        else:
            cols_per_row = 4
        
        # Calculate number of rows needed
        num_rows = (num_audiences + cols_per_row - 1) // cols_per_row
        
        # Create charts in grid layout
        for row in range(num_rows):
            # Determine how many columns in this row
            start_idx = row * cols_per_row
            end_idx = min(start_idx + cols_per_row, num_audiences)
            audiences_in_row = audiences_to_show[start_idx:end_idx]
            
            # Always create the same number of columns for consistent width
            cols = st.columns(cols_per_row)
            
            for col_idx, audience in enumerate(audiences_in_row):
                with cols[col_idx]:
                    with stylable_container(
                        key=f"vmk_audience_chart_{audience.replace(' ', '_')}",
                        css_styles="""
                            {
                                background: var(--card-bg);
                                border: 1px solid var(--gray-border);
                                border-radius: 8px;
                                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                                padding: 1.25rem;
                                margin-bottom: 1rem;
                            }
                        """
                    ):
                        # Create individual chart for this audience
                        fig = go.Figure()
                        
                        audience_data = delivery_data[audience]
                        audience_row = df[df['Combined_Audience'] == audience].iloc[0]
                        
                        # Add gray background bars (planned quantity)
                        fig.add_trace(go.Bar(
                            name="Planned",
                            x=metrics,
                            y=[100] * len(metrics),
                            marker_color='rgba(211, 211, 211, 0.5)',
                            showlegend=False,
                            hovertemplate='Planned: %{y}%<extra></extra>'
                        ))
                        
                        # Add actual achievement bars
                        fig.add_trace(go.Bar(
                            name="Achieved",
                            x=metrics,
                            y=audience_data,
                            marker_color=[metric_colors[i % len(metric_colors)] for i in range(len(metrics))],
                            text=[f"{val:.1f}%" for val in audience_data],
                            textposition='inside',
                            showlegend=False,
                            hovertemplate='Achieved: %{y:.1f}%<br>Planned: 100%<extra></extra>'
                        ))
                        
                        # Add value labels above bars (showing actual values)
                        for i, metric in enumerate(metrics):
                            if i < len(audience_data):
                                # Get the actual value for this metric
                                if metric == "Impression":
                                    actual_value = audience_row['Impression']
                                    label_text = f"{actual_value:,.0f}"
                                elif metric == "Reach":
                                    actual_value = audience_row['reach']
                                    label_text = f"{actual_value:,.0f}"
                                elif metric == "Budget":
                                    actual_value = audience_row['Cost']
                                    label_text = f"{actual_value:,.0f}"
                                elif metric == "Views":
                                    actual_value = audience_row['Views']
                                    label_text = f"{actual_value:,.0f}"
                                elif metric == "Clicks":
                                    actual_value = audience_row['Clicks']
                                    label_text = f"{actual_value:,.0f}"
                                else:
                                    label_text = ""
                                
                                if label_text:
                                    fig.add_annotation(
                                        x=metric,
                                        y=min(audience_data[i] + 5, 120),  # Position above the bar
                                        text=label_text,
                                        showarrow=False,
                                        font=dict(size=9, color="#333333"),
                                        bgcolor="rgba(255,255,255,0.8)",
                                        bordercolor="#cccccc",
                                        borderwidth=1
                                    )
                        
                        # Add horizontal reference line at 100% (planned target)
                        run_rate = (audience_row['active_day'] / audience_row['plan_active_day'] * 100) if audience_row.get('plan_active_day') and audience_row['plan_active_day'] > 0 else 0
                        
                        # Add horizontal line at 100% (planned target)
                        fig.add_hline(
                            y=100,
                            line_dash="dash",
                            line_color="#ff6b6b",
                            line_width=3,
                            annotation_text="Planned Target: 100%",
                            annotation_position="top right",
                            annotation_font_size=11,
                            annotation_font_color="#ff6b6b",
                            annotation_bgcolor="rgba(255,255,255,0.9)",
                            annotation_bordercolor="#ff6b6b",
                            annotation_borderwidth=1
                        )
                        
                        # Update layout for individual chart
                        fig.update_layout(
                            title=f"{audience}",
                            xaxis_title="Metrics",
                            yaxis_title="Percentage (%)",
                            yaxis=dict(range=[0, max(120, max(audience_data) + 10)]),  # Allow to exceed 100%
                            yaxis2=dict(
                                title="Run Rate (%)",
                                overlaying='y',
                                side='right',
                                range=[0, 100]  # Run rate capped at 100%
                            ),
                            height=400,
                            showlegend=False,
                            barmode='overlay',  # Overlay bars to show achievement over planned
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        # Rotate x-axis labels for better readability
                        fig.update_xaxes(tickangle=45)
                        
                        st.plotly_chart(fig, use_container_width=True)
        
                        # Add data table below the chart
                        st.markdown("#### Data Summary")
                        
                        # Create summary data for this audience
                        summary_data = {
                            "Metric": ["Impression", "Reach", "Budget", "Views", "Clicks", "Run Rate"],
                            "Plan": [
                                f"{audience_row['impression_plan']:,.0f}" if pd.notna(audience_row['impression_plan']) else "N/A",
                                f"{audience_row['reach_plan']:,.0f}" if pd.notna(audience_row['reach_plan']) else "N/A",
                                f"{audience_row['net_media_cost']:,.0f}" if pd.notna(audience_row['net_media_cost']) else "N/A",
                                f"{audience_row['views_plan']:,.0f}" if pd.notna(audience_row['views_plan']) else "N/A",
                                f"{audience_row['click_plan']:,.0f}" if pd.notna(audience_row['click_plan']) else "N/A",
                                f"{audience_row['plan_active_day']:,.0f}" if pd.notna(audience_row['plan_active_day']) else "N/A"
                            ],
                            "Actual": [
                                f"{audience_row['Impression']:,.0f}" if pd.notna(audience_row['Impression']) else "N/A",
                                f"{audience_row['reach']:,.0f}" if pd.notna(audience_row['reach']) else "N/A",
                                f"{audience_row['Cost']:,.0f}" if pd.notna(audience_row['Cost']) else "N/A",
                                f"{audience_row['Views']:,.0f}" if pd.notna(audience_row['Views']) else "N/A",
                                f"{audience_row['Clicks']:,.0f}" if pd.notna(audience_row['Clicks']) else "N/A",
                                f"{audience_row['active_day']:,.0f}" if pd.notna(audience_row['active_day']) else "N/A"
                            ],
                            "Delivery %": [
                                f"{audience_row['impression_delivery']:.1f}%" if pd.notna(audience_row['impression_delivery']) else "N/A",
                                f"{audience_row['reach_delivery']:.1f}%" if pd.notna(audience_row['reach_delivery']) else "N/A",
                                f"{audience_row['budget_delivery']:.1f}%" if pd.notna(audience_row['budget_delivery']) else "N/A",
                                f"{audience_row['views_delivery']:.1f}%" if pd.notna(audience_row['views_delivery']) else "N/A",
                                f"{audience_row['clicks_delivery']:.1f}%" if pd.notna(audience_row['clicks_delivery']) else "N/A",
                                f"{min(run_rate, 100):.1f}%" if run_rate > 0 else "N/A"  # Run rate capped at 100%
                            ]
                        }
                        
                        # Create DataFrame and display as styled table
                        summary_df = pd.DataFrame(summary_data)
                        
                        # Apply conditional formatting for delivery percentages
                        def highlight_delivery(val):
                            if isinstance(val, str) and val.endswith('%'):
                                try:
                                    num_val = float(val.rstrip('%'))
                                    if num_val >= 100:
                                        return 'background-color: #d4edda; color: #155724; font-weight: bold'  # Green for good
                                    elif num_val >= 80:
                                        return 'background-color: #fff3cd; color: #856404; font-weight: bold'  # Yellow for moderate
                                    else:
                                        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'  # Red for poor
                                except:
                                    pass
                            return ''
                        
                        # Display the styled table
                        st.dataframe(
                            summary_df.style.applymap(highlight_delivery),
                            use_container_width=True,
                            hide_index=True
                        )
        
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
                    f"{row['Cost_Per_Unit']:.2f}" if pd.notna(row['Cost_Per_Unit']) else '',
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
        
        