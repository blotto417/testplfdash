import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from streamlit_extras.stylable_container import stylable_container
from st_aggrid import AgGrid, GridOptionsBuilder

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
        columns = ["Region", "Code", "Impression", "Cost", "Clicks"]
        
        df = query_data(columns, table, filters=active_filters, start_date=start_date, end_date=end_date)

        if df.empty:
            st.warning("No region data available for the selected filters.")
            return

        df_grouped = df.groupby(["Region", "Code"]).agg({
            "Impression": "sum",
            "Cost": "sum",
            "Clicks": "sum"
        }).reset_index()

        json_path = os.path.join("region", "vietnam_state.geojson")
        with open(json_path, "r", encoding="utf-8") as f:
            vietnam_geo = json.load(f)

        # --- Chart and Container Heights ---
        # Set a base height. The map and the two bar charts will conform to this.
        chart_height = 700
        
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

        # Bar Chart 1: Impressions and CPM
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=df_top10['Region'], y=df_top10['Impression'], name='Impressions', marker_color='dodgerblue', yaxis='y1'))
        fig1.add_trace(go.Scatter(x=df_top10['Region'], y=df_top10['CPM'], name='CPM', mode='lines+markers', line=dict(color='mediumorchid'), yaxis='y2'))
        fig1.update_layout(
            title='Top 10 Regions by Impressions and CPM', 
            yaxis=dict(title='Impressions'), 
            yaxis2=dict(title='CPM', overlaying='y', side='right'), 
            legend=dict(x=0.1, y=1.1, orientation='h'),
            height=chart_height / 2, # Half of the total height
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)'
        )

        # Bar Chart 2: Clicks and CTR
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df_top10['Region'], y=df_top10['Clicks'], name='Clicks', marker_color='dodgerblue', yaxis='y1'))
        fig2.add_trace(go.Scatter(x=df_top10['Region'], y=df_top10['CTR'], name='CTR', mode='lines+markers', line=dict(color='mediumorchid'), yaxis='y2'))
        fig2.update_layout(
            title='Top 10 Regions by Clicks and CTR', 
            yaxis=dict(title='Clicks'), 
            yaxis2=dict(title='CTR (%)', overlaying='y', side='right'), 
            legend=dict(x=0.1, y=1.1, orientation='h'),
            height=chart_height / 2, # Half of the total height
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)'
        )

        # --- Layout ---
        col1, col2 = st.columns([1.8, 3])
        
        # Column 1: Map
        with col1:
            with stylable_container(
                key="vmk_map_container",
                css_styles=f"""
                    {{
                        background: var(--card-bg);
                        border: 1px solid var(--gray-border);
                        border-radius: 8px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                        padding: 1.25rem;
                        height: {chart_height + 50}px;
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
                        height: {chart_height + 50}px;
                    }}
                """
            ):
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
                    st.header(platform)
                    platform_filters = active_filters.copy()
                    platform_filters["Platform"] = platform
                    df_platform = query_data(
                        ["Region", "Cost", "Impression", "Clicks"], 
                        "report_campaign_region_api2", 
                        platform_filters, 
                        start_date, 
                        end_date,
                        aggregations={"Cost": "SUM", "Impression": "SUM", "Clicks": "SUM"},
                        group_by=["Region"]
                    )
                    if not df_platform.empty:
                        gb = GridOptionsBuilder.from_dataframe(df_platform)
                        gb.configure_column("Cost", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Cost.toLocaleString('en-US')")
                        gb.configure_column("Impression", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Impression.toLocaleString('en-US')")
                        AgGrid(df_platform, gridOptions=gb.build(), key=f"maptable_{platform}", height=400)
                    else:
                        st.warning(f"No data for {platform}.")