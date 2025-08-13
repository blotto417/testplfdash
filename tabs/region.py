import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from streamlit_extras.stylable_container import stylable_container
from streamlit_elements import elements, mui, html
from tabs.formatters import center_header_css

def display(query_data, active_filters, start_date, end_date):
    with stylable_container(
        key="region_container",
        css_styles="""
            {
                animation: fadeIn 0.5s ease-in-out;
            }
            """,
    ):
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
                ">Region Performance</p>
            </div>
            """,
            unsafe_allow_html=True
        )    

        table = "report_campaign_region_api2"
        columns = ["Region", "Code", "Impression", "Cost", "Clicks", "Views"]
        
        df = query_data(columns, table, filters=active_filters, start_date=start_date, end_date=end_date)
        if df.empty:
            st.warning("No region data available for the selected filters.")
            return

        df_grouped = df.groupby(["Region", "Code"]).agg({
            "Impression": "sum",
            "Cost": "sum",
            "Clicks": "sum",
            "Views": "sum"
        }).reset_index()

        json_path = os.path.join("region", "vietnam_state.geojson")
        with open(json_path, "r", encoding="utf-8") as f:
            vietnam_geo = json.load(f)

        # --- Chart and Container Heights ---
        # Set a base height. The map and the two bar charts will conform to this.
        chart_height = 700
        
        # Helper function to format numbers with K, M suffixes
        def format_number(value):
            if value >= 1_000_000:
                return f'{value/1_000_000:.1f}M'
            elif value >= 1_000:
                return f'{value/1_000:.1f}K'
            else:
                return f'{value:.0f}'

        # --- Layout ---
        col1, col2 = st.columns([1.8, 3])
        
        # Column 1: Map
        with col1:
            # --- Choropleth Map ---
            fig = px.choropleth_mapbox(
                df_grouped,
                locations='Code',
                featureidkey="properties.Code",
                geojson=vietnam_geo,
                color='Impression',
                hover_name="Region",
                mapbox_style="carto-positron",
                center={"lat": 16, "lon": 106},
                zoom=4.5,
                title="Impression by Region",
            )
            fig.update_geos(fitbounds="geojson", visible=False)
            fig.update_layout(
                height=chart_height, 
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=40, b=0)
            )

            # --- Bar Charts ---
            df_grouped['CPM'] = (df_grouped['Cost'] / df_grouped['Impression']) * 1000
            df_grouped['CTR'] = (df_grouped['Clicks'] / df_grouped['Impression']) * 100
            df_top10 = df_grouped.sort_values(by='Impression', ascending=False).head(10)
            
            # Helper function to format numbers with K, M suffixes
            def format_number(value):
                if value >= 1_000_000:
                    return f'{value/1_000_000:.1f}M'
                elif value >= 1_000:
                    return f'{value/1_000:.1f}K'
                else:
                    return f'{value:.0f}'

            with stylable_container(
                key="vmk_map_container",
                css_styles=f"""
                    {{
                        background: var(--card-bg);
                        border: 1px solid var(--gray-border);
                        border-radius: 8px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                        padding: 1.25rem;
                        height: {chart_height + 150}px;
                    }}
                """
            ):
                st.plotly_chart(fig, use_container_width=True)
        
        # Column 2: Bar Charts
        with col2:
            with stylable_container(
                key="vmk_top10_container",
                css_styles=f"""
                    {{
                        background: var(--card-bg);
                        border: 1px solid var(--gray-border);
                        border-radius: 8px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                        padding: 1.25rem;
                        height: {chart_height + 150}px;
                    }}
                """
            ):
                # Add metric filter inside the chart container
                metric_col1, metric_col2, metric_col3 = st.columns([1, 1, 1])
                
                with metric_col3:
                    selected_metric = st.selectbox(
                        "Select Metric for Charts",
                        options=["CPM", "CPV", "CPC"],
                        index=0,
                        key="region_metric_selector",
                        help="CPM: Cost Per Mille (per 1000 impressions), CPV: Cost Per View, CPC: Cost Per Click"
                    )
                
                # with metric_col2:
                #     # Show summary statistics for the selected metric
                #     if selected_metric in df_grouped.columns:
                #         avg_metric = df_grouped[selected_metric].mean()
                #         if selected_metric == "CPM":
                #             st.metric("Avg CPM", f"{format_number(avg_metric)}")
                #         elif selected_metric == "CPV":
                #             st.metric("Avg CPV", f"{format_number(avg_metric)}")
                #         elif selected_metric == "CPC":
                #             st.metric("Avg CPC", f"{format_number(avg_metric)}")
                
                # Calculate all metrics with safe division
                df_grouped['CPM'] = df_grouped.apply(lambda row: (row['Cost'] / row['Impression'] * 1000) if row['Impression'] > 0 else 0, axis=1)
                df_grouped['CPV'] = df_grouped.apply(lambda row: (row['Cost'] / row['Views']) if row['Views'] > 0 else 0, axis=1)
                df_grouped['CPC'] = df_grouped.apply(lambda row: (row['Cost'] / row['Clicks']) if row['Clicks'] > 0 else 0, axis=1)
                df_grouped['CTR'] = df_grouped.apply(lambda row: (row['Clicks'] / row['Impression'] * 100) if row['Impression'] > 0 else 0, axis=1)
                
                # Get the selected metric values
                if selected_metric == "CPM":
                    metric_title = "CPM"
                    metric_format = lambda x: format_number(x)
                elif selected_metric == "CPV":
                    metric_title = "CPV"
                    metric_format = lambda x: format_number(x)
                elif selected_metric == "CPC":
                    metric_title = "CPC"
                    metric_format = lambda x: format_number(x)
                
                # Check if the selected metric has valid data
                if selected_metric == "CPV" and df_grouped['Views'].sum() == 0:
                    st.warning("⚠️ No view data available. CPV will show 0 for all regions.")
                elif selected_metric == "CPC" and df_grouped['Clicks'].sum() == 0:
                    st.warning("⚠️ No click data available. CPC will show 0 for all regions.")
                
                df_top10 = df_grouped.sort_values(by='Impression', ascending=False).head(10)
                
                # Bar Chart 1: Impressions and Selected Metric
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(x=df_top10['Region'], y=df_top10['Impression'], name='Impressions', marker_color='dodgerblue', yaxis='y1'))
                fig1.add_trace(go.Scatter(
                    x=df_top10['Region'], 
                    y=df_top10[selected_metric], 
                    name=selected_metric, 
                    mode='lines+markers+text', 
                    line=dict(color='#FF6B35', width=3),  # Orange color for better contrast
                    marker=dict(color='#FF6B35', size=8),
                    yaxis='y2',
                    text=[metric_format(val) for val in df_top10[selected_metric]],  # Use selected metric format
                    textposition='top center',  # Back to top center positioning
                    textfont=dict(size=11, color='#2C3E50'),  # Back to original font size
                    texttemplate='<b>%{text}</b>',  # Bold text
                ))
                fig1.update_layout(
                    title=f'Top 10 Regions by Impressions and {selected_metric}', 
                    yaxis=dict(
                        title='Impressions', 
                        showgrid=False,
                        tickformat='.2s'  # Short format (K, M)
                    ), 
                    yaxis2=dict(title=metric_title, overlaying='y', side='right', showgrid=False), 
                    xaxis=dict(showgrid=False),
                    legend=dict(x=0.1, y=1.1, orientation='h'),
                    height=int((chart_height / 2)), # Half of the total height + 10%
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=50, r=80, t=80, b=50)  # Increased top margin for labels
                )

                # Bar Chart 2: Clicks and CTR
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=df_top10['Region'], y=df_top10['Clicks'], name='Clicks', marker_color='dodgerblue', yaxis='y1'))
                fig2.add_trace(go.Scatter(
                    x=df_top10['Region'], 
                    y=df_top10['CTR'], 
                    name='CTR', 
                    mode='lines+markers+text', 
                    line=dict(color='#E74C3C', width=3),  # Red color for better contrast
                    marker=dict(color='#E74C3C', size=8),
                    yaxis='y2',
                    text=[f'{val:.2f}%' for val in df_top10['CTR']],
                    textposition='top center',  # Back to top center positioning
                    textfont=dict(size=11, color='#2C3E50'),  # Back to original font size
                    texttemplate='<b>%{text}</b>',  # Bold text
                ))
                fig2.update_layout(
                    title='Top 10 Regions by Clicks and CTR', 
                    yaxis=dict(
                        title='Clicks', 
                        showgrid=False,
                        tickformat='.2s'  # Short format (K, M)
                    ), 
                    yaxis2=dict(title='CTR (%)', overlaying='y', side='right', showgrid=False), 
                    xaxis=dict(showgrid=False),
                    legend=dict(x=0.1, y=1.1, orientation='h'),
                    height=int((chart_height / 2) * 1.1), # Half of the total height + 10%
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=50, r=80, t=80, b=50)  # Increased top margin for labels
                )
                
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig2, use_container_width=True)

        # --- Platform Breakdown Tables ---
        st.subheader("Platform Breakdown")
        col_yt, col_fb, col_tk = st.columns(3)
        platforms = ["YouTube", "Facebook", "TikTok"]
        cols = [col_yt, col_fb, col_tk]

        for platform, col in zip(platforms, cols):
            with col:
                with stylable_container(
                    key=f"vmk_platform_container_{platform}",
                    css_styles=f"""
                        {{
                            background: var(--card-bg);
                            border: 1px solid var(--gray-border);
                            border-radius: 8px;
                            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                            padding: 1.25rem;
                        }}
                    """
                ):
                    # Update header for YouTube to show it includes Google platforms
                    if platform == "YouTube":
                        st.header("YouTube & Google")
                    else:
                        st.header(platform)
                    
                    platform_filters = active_filters.copy()
                    
                    # Special handling for YouTube to include Google platforms
                    if platform == "YouTube":
                        # Get all data first, then filter for YouTube or Google platforms
                        df_all_platforms = query_data(
                            ["Funnel", "Region", "Format", "Audience", "Platform", "Cost", "Impression", "Views", "Clicks"], 
                            "report_campaign_region_api2", 
                            active_filters, 
                            start_date, 
                            end_date,
                            aggregations=None,  # No aggregations to get individual rows
                            group_by=None
                        )
                        
                        # Filter for YouTube or platforms containing "Google"
                        if not df_all_platforms.empty:
                            youtube_google_mask = (
                                (df_all_platforms['Platform'] == 'YouTube') | 
                                (df_all_platforms['Platform'].str.contains('Google', case=False, na=False))
                            )
                            df_filtered = df_all_platforms[youtube_google_mask]
                            
                            # Now aggregate the filtered data
                            if not df_filtered.empty:
                                df_platform = df_filtered.groupby(["Funnel", "Region", "Format", "Audience"]).agg({
                                    "Cost": "sum",
                                    "Impression": "sum",
                                    "Views": "sum",
                                    "Clicks": "sum"
                                }).reset_index()
                            else:
                                df_platform = pd.DataFrame()
                        else:
                            df_platform = pd.DataFrame()
                    else:
                        # Regular platform filtering for Facebook and TikTok
                        platform_filters["Platform"] = platform
                        df_platform = query_data(
                            ["Funnel", "Region", "Format", "Audience", "Cost", "Impression", "Views", "Clicks"], 
                            "report_campaign_region_api2", 
                            platform_filters, 
                            start_date, 
                            end_date,
                            aggregations={"Cost": "SUM", "Impression": "SUM", "Views": "SUM", "Clicks": "SUM"},
                            group_by=["Funnel", "Region", "Format", "Audience"]
                        )
                    
                    if not df_platform.empty:
                        # Ensure all required columns exist, add default values if missing
                        required_columns = ["Funnel", "Region", "Format", "Audience", "Cost", "Impression", "Views", "Clicks"]
                        for col in required_columns:
                            if col not in df_platform.columns:
                                if col in ["Funnel", "Format", "Audience"]:
                                    df_platform[col] = "N/A"
                                elif col == "Views":
                                    df_platform[col] = 0
                        
                        # Convert to float to avoid decimal/float type errors
                        df_platform['Cost'] = df_platform['Cost'].astype(float)
                        df_platform['Impression'] = df_platform['Impression'].astype(float)
                        df_platform['Views'] = df_platform['Views'].astype(float)
                        df_platform['Clicks'] = df_platform['Clicks'].astype(float)
                        df_platform = df_platform.sort_values('Impression', ascending=False)
                        
                        # Create Material-UI Table
                        with elements(f"region_table_{platform}"):
                            with mui.Paper(
                                elevation=0,
                                sx={
                                    "margin": "10px 0",
                                    "border": "1px solid #e2e8f0",
                                    "overflow": "hidden",
                                    "background": "#ffffff"
                                }
                            ):
                                with mui.TableContainer(sx={"maxHeight": 400, "position": "relative"}):
                                    with mui.Table(stickyHeader=True, size="small"):
                                        # Table Header
                                        with mui.TableHead():
                                            with mui.TableRow():
                                                headers = ["Funnel", "Region", "Format", "Audience", "Cost", "Impression", "Views", "Clicks"]
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
                                            for _, row in df_platform.iterrows():
                                                with mui.TableRow(
                                                    sx={
                                                        "&:hover": {
                                                            "backgroundColor": "#f8fafc"
                                                        }
                                                    }
                                                ):
                                                    # Funnel
                                                    mui.TableCell(
                                                        str(row.get('Funnel', 'N/A')),
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                                    # Region
                                                    mui.TableCell(
                                                        str(row['Region']),
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                                    # Format
                                                    mui.TableCell(
                                                        str(row.get('Format', 'N/A')),
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                                    # Audience
                                                    mui.TableCell(
                                                        str(row.get('Audience', 'N/A')),
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                                    # Cost
                                                    mui.TableCell(
                                                        f"{row['Cost']:,.0f}",
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                                    # Impression
                                                    mui.TableCell(
                                                        f"{row['Impression']:,.0f}",
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                                    # Views
                                                    mui.TableCell(
                                                        f"{row.get('Views', 0):,.0f}",
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                                    # Clicks
                                                    mui.TableCell(
                                                        f"{row['Clicks']:,.0f}",
                                                        sx={
                                                            "textAlign": "center",
                                                            "padding": "6px 4px",
                                                            "fontSize": "0.7rem",
                                                            "fontWeight": "normal",
                                                            "borderBottom": "1px solid #e2e8f0",
                                                            "borderRight": "1px solid #e2e8f0"
                                                        }
                                                    )
                                        
                                        # Calculate totals for sticky footer
                                        total_cost = df_platform['Cost'].sum()
                                        total_impression = df_platform['Impression'].sum()
                                        total_views = df_platform['Views'].sum()
                                        total_clicks = df_platform['Clicks'].sum()
                                        
                                        # Sticky Table Footer
                                        with mui.TableFooter(
                                            sx={
                                                "position": "sticky",
                                                "bottom": 0,
                                                "backgroundColor": "#f8f9fa",
                                                "zIndex": 10,
                                                "borderTop": "2px solid #003366"
                                            }
                                        ):
                                            with mui.TableRow():
                                                # TOTAL label (spans 4 columns for Funnel, Region, Format, Audience)
                                                mui.TableCell(
                                                    "TOTAL",
                                                    sx={
                                                        "textAlign": "center",
                                                        "padding": "8px 6px",
                                                        "fontSize": "0.75rem",
                                                        "fontWeight": "bold",
                                                        "color": "#003366",
                                                        "backgroundColor": "#f8f9fa",
                                                        "borderBottom": "1px solid #e2e8f0",
                                                        "borderRight": "1px solid #e2e8f0"
                                                    },
                                                    colSpan=4
                                                )
                                                # Total Cost
                                                mui.TableCell(
                                                    f"{total_cost:,.0f}",
                                                    sx={
                                                        "textAlign": "center",
                                                        "padding": "8px 6px",
                                                        "fontSize": "0.75rem",
                                                        "fontWeight": "bold",
                                                        "color": "#003366",
                                                        "backgroundColor": "#f8f9fa",
                                                        "borderBottom": "1px solid #e2e8f0",
                                                        "borderRight": "1px solid #e2e8f0"
                                                    }
                                                )
                                                # Total Impression
                                                mui.TableCell(
                                                    f"{total_impression:,.0f}",
                                                    sx={
                                                        "textAlign": "center",
                                                        "padding": "8px 6px",
                                                        "fontSize": "0.75rem",
                                                        "fontWeight": "bold",
                                                        "color": "#003366",
                                                        "backgroundColor": "#f8f9fa",
                                                        "borderBottom": "1px solid #e2e8f0",
                                                        "borderRight": "1px solid #e2e8f0"
                                                    }
                                                )
                                                # Total Views
                                                mui.TableCell(
                                                    f"{total_views:,.0f}",
                                                    sx={
                                                        "textAlign": "center",
                                                        "padding": "8px 6px",
                                                        "fontSize": "0.75rem",
                                                        "fontWeight": "bold",
                                                        "color": "#003366",
                                                        "backgroundColor": "#f8f9fa",
                                                        "borderBottom": "1px solid #e2e8f0",
                                                        "borderRight": "1px solid #e2e8f0"
                                                    }
                                                )
                                                # Total Clicks
                                                mui.TableCell(
                                                    f"{total_clicks:,.0f}",
                                                    sx={
                                                        "textAlign": "center",
                                                        "padding": "8px 6px",
                                                        "fontSize": "0.75rem",
                                                        "fontWeight": "bold",
                                                        "color": "#003366",
                                                        "backgroundColor": "#f8f9fa",
                                                        "borderBottom": "1px solid #e2e8f0",
                                                        "borderRight": "1px solid #e2e8f0"
                                                    }
                                                )
                    else:
                        st.warning(f"No data for {platform}.")

        # --- Effectiveness and Efficiency Tables ---
        with stylable_container(
            key="effectiveness_efficiency_container",
            css_styles="""
                {
                    background: var(--card-bg);
                    border: 1px solid var(--gray-border);
                    border-radius: 8px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    padding: 1.25rem;
                    margin-top: 2rem;
                }
            """
        ):
            # EFFECTIVENESS Table
            st.subheader("EFFECTIVENESS")
            
            # Query data for Effectiveness table
            # First, let's try to get the data with all dimensions
            try:
                effectiveness_df = query_data(
                    ["Region", "Brand", "Funnel", "Platform", "Format", "Audience", "Clicks", "Views", "Impression"], 
                    table, 
                    filters=active_filters, 
                    start_date=start_date, 
                    end_date=end_date,
                    aggregations={"Clicks": "SUM", "Views": "SUM", "Impression": "SUM"},
                    group_by=["Region", "Brand", "Funnel", "Platform", "Format", "Audience"]
                )
            except:
                # If the query fails, fallback to basic columns
                effectiveness_df = query_data(
                    ["Region", "Clicks", "Impression"], 
                    table, 
                    filters=active_filters, 
                    start_date=start_date, 
                    end_date=end_date,
                    aggregations={"Clicks": "SUM", "Views": "SUM"},
                    group_by=["Region"]
                )
                
                # Add missing columns with default values
                if not effectiveness_df.empty:
                    effectiveness_df["Brand"] = "N/A"
                    effectiveness_df["Funnel"] = "N/A"
                    effectiveness_df["Platform"] = "N/A"
                    effectiveness_df["Format"] = "N/A"
                    effectiveness_df["Audience"] = "N/A"
                    effectiveness_df["Views"] = 0
                
                # Reorder columns to match the requested structure
                effectiveness_df = effectiveness_df[["Region", "Brand", "Funnel", "Platform", "Format", "Audience", "Clicks", "Views", "Impression"]]
            
            if not effectiveness_df.empty:
                # Convert numeric columns to float to avoid dtype errors
                effectiveness_df['Clicks'] = pd.to_numeric(effectiveness_df['Clicks'], errors='coerce').fillna(0)
                effectiveness_df['Views'] = pd.to_numeric(effectiveness_df['Views'], errors='coerce').fillna(0)
                effectiveness_df['Impression'] = pd.to_numeric(effectiveness_df['Impression'], errors='coerce').fillna(0)
                
                # Calculate VTR and CTR with safe division
                effectiveness_df['VTR'] = np.where(
                    effectiveness_df['Impression'] > 0,
                    (effectiveness_df['Views'] / effectiveness_df['Impression'] * 100).round(2),
                    0
                )
                effectiveness_df['CTR'] = np.where(
                    effectiveness_df['Impression'] > 0,
                    (effectiveness_df['Clicks'] / effectiveness_df['Impression'] * 100).round(2),
                    0
                )
                
                # Sort by VTR descending
                effectiveness_df = effectiveness_df.sort_values('VTR', ascending=False)
                
                # Display the table
                with elements("effectiveness_table"):
                    with mui.Paper(
                        elevation=0,
                        sx={
                            "margin": "10px 0",
                            "border": "1px solid #e2e8f0",
                            "overflow": "hidden",
                            "background": "#ffffff"
                        }
                    ):
                        with mui.TableContainer(sx={"maxHeight": 400, "position": "relative"}):
                            with mui.Table(stickyHeader=True, size="small"):
                                # Table Header
                                with mui.TableHead():
                                    with mui.TableRow():
                                        headers = ["Region", "Brand", "Funnel", "Platform", "Format", "Audience", "Clicks", "Views", "Impression", "VTR (%)", "CTR (%)"]
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
                                    for _, row in effectiveness_df.iterrows():
                                        with mui.TableRow(
                                            sx={
                                                "&:hover": {
                                                    "backgroundColor": "#f8fafc"
                                                }
                                            }
                                        ):
                                            # Region
                                            mui.TableCell(
                                                str(row['Region']),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Brand
                                            mui.TableCell(
                                                str(row.get('Brand', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Funnel
                                            mui.TableCell(
                                                str(row.get('Funnel', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Platform
                                            mui.TableCell(
                                                str(row.get('Platform', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Format
                                            mui.TableCell(
                                                str(row.get('Format', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Audience
                                            mui.TableCell(
                                                str(row.get('Audience', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Clicks
                                            mui.TableCell(
                                                f"{row['Clicks']:,.0f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Views
                                            mui.TableCell(
                                                f"{row['Views']:,.0f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Impression
                                            mui.TableCell(
                                                f"{row['Impression']:,.0f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # VTR
                                            mui.TableCell(
                                                f"{row['VTR']:.2f}%",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # CTR
                                            mui.TableCell(
                                                f"{row['CTR']:.2f}%",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
            else:
                st.warning("No effectiveness data available.")

            # EFFICIENCY Table
            st.subheader("EFFICIENCY")
            
            # Query data for Efficiency table
            try:
                efficiency_df = query_data(
                    ["Region", "Brand", "Funnel", "Platform", "Format", "Audience", "Cost", "Views", "Impression"], 
                    table, 
                    filters=active_filters, 
                    start_date=start_date, 
                    end_date=end_date,
                    aggregations={"Cost": "SUM", "Views": "SUM", "Impression": "SUM"},
                    group_by=["Region", "Brand", "Funnel", "Platform", "Format", "Audience"]
                )
            except:
                # If the query fails, fallback to basic columns
                efficiency_df = query_data(
                    ["Region", "Cost", "Impression"], 
                    table, 
                    filters=active_filters, 
                    start_date=start_date, 
                    end_date=end_date,
                    aggregations={"Cost": "SUM", "Views": "SUM"},
                    group_by=["Region"]
                )
                
                # Add missing columns with default values
                if not efficiency_df.empty:
                    efficiency_df["Brand"] = "N/A"
                    efficiency_df["Funnel"] = "N/A"
                    efficiency_df["Platform"] = "N/A"
                    efficiency_df["Format"] = "N/A"
                    efficiency_df["Audience"] = "N/A"
                    efficiency_df["Views"] = 0
                
                # Reorder columns to match the requested structure
                efficiency_df = efficiency_df[["Region", "Brand", "Funnel", "Platform", "Format", "Audience", "Cost", "Views", "Impression"]]
            
            if not efficiency_df.empty:
                # Convert numeric columns to float to avoid dtype errors
                efficiency_df['Cost'] = pd.to_numeric(efficiency_df['Cost'], errors='coerce').fillna(0)
                efficiency_df['Views'] = pd.to_numeric(efficiency_df['Views'], errors='coerce').fillna(0)
                efficiency_df['Impression'] = pd.to_numeric(efficiency_df['Impression'], errors='coerce').fillna(0)
                
                # Calculate CPV and CPM with safe division
                efficiency_df['CPV'] = np.where(
                    efficiency_df['Views'] > 0,
                    (efficiency_df['Cost'] / efficiency_df['Views']).round(2),
                    0
                )
                efficiency_df['CPM'] = np.where(
                    efficiency_df['Impression'] > 0,
                    (efficiency_df['Cost'] / efficiency_df['Impression'] * 1000).round(2),
                    0
                )
                
                # Sort by CPV ascending (lower is better)
                efficiency_df = efficiency_df.sort_values('CPV', ascending=True)
                
                # Display the table
                with elements("efficiency_table"):
                    with mui.Paper(
                        elevation=0,
                        sx={
                            "margin": "10px 0",
                            "border": "1px solid #e2e8f0",
                            "overflow": "hidden",
                            "background": "#ffffff"
                        }
                    ):
                        with mui.TableContainer(sx={"maxHeight": 400, "position": "relative"}):
                            with mui.Table(stickyHeader=True, size="small"):
                                # Table Header
                                with mui.TableHead():
                                    with mui.TableRow():
                                        headers = ["Region", "Brand", "Funnel", "Platform", "Format", "Audience", "Cost", "Views", "Impression", "CPV", "CPM"]
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
                                    for _, row in efficiency_df.iterrows():
                                        with mui.TableRow(
                                            sx={
                                                "&:hover": {
                                                    "backgroundColor": "#f8fafc"
                                                }
                                            }
                                        ):
                                            # Region
                                            mui.TableCell(
                                                str(row['Region']),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Brand
                                            mui.TableCell(
                                                str(row.get('Brand', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Funnel
                                            mui.TableCell(
                                                str(row.get('Funnel', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Platform
                                            mui.TableCell(
                                                str(row.get('Platform', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Format
                                            mui.TableCell(
                                                str(row.get('Format', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Audience
                                            mui.TableCell(
                                                str(row.get('Audience', 'N/A')),
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Cost
                                            mui.TableCell(
                                                f"{row['Cost']:,.0f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Views
                                            mui.TableCell(
                                                f"{row['Views']:,.0f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # Impression
                                            mui.TableCell(
                                                f"{row['Impression']:,.0f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # CPV
                                            mui.TableCell(
                                                f"{row['CPV']:.2f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
                                            # CPM
                                            mui.TableCell(
                                                f"{row['CPM']:.2f}",
                                                sx={
                                                    "textAlign": "center",
                                                    "padding": "6px 4px",
                                                    "fontSize": "0.7rem",
                                                    "fontWeight": "normal",
                                                    "borderBottom": "1px solid #e2e8f0",
                                                    "borderRight": "1px solid #e2e8f0"
                                                }
                                            )
            else:
                st.warning("No efficiency data available.")
