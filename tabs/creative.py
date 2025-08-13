import streamlit as st
import pandas as pd
import altair as alt
from streamlit_extras.stylable_container import stylable_container
from streamlit_elements import elements, mui, html
from tabs.formatters import center_header_css

def generate_platform_analysis(platform_name, query_data, active_filters, start_date, end_date):
    """
    Generates the benchmark analysis section for a specific platform,
    correctly mapping 'Content' to the x-axis.
    """
   
    with stylable_container(
        key=f"{platform_name.lower()}BenchmarkAnalysis",
        css_styles="""
            {
                background-color: white;
                border-radius: 0.5em;
                padding: 0.5em;
                margin-bottom: 1em;
            }
        """,
    ):

        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(f"{platform_name} Benchmark Analysis")
        with col2:
            metric_choice = st.selectbox(
                label="Select metrics",
                options=["CTR"], # Currently only CTR is calculated
                key=f"{platform_name.lower()}_metric_selectbox"
            )

        # --- Data Fetching and Processing ---
        platform_filters = active_filters.copy()
        # Only add the platform filter if one isn't already specified in the main filters
        if "Platform" not in platform_filters:
            platform_filters["Platform"] = platform_name
        query_columns = ["Format", "Creative_Type", "Creative_Length", "Content", "Clicks", "Impression", "ctr_bm"]
        df_platform = query_data(
            columns=query_columns,
            tablename="report_campaign_creative",
            filters=platform_filters,
            start_date=start_date,
            end_date=end_date
        )
        
        if df_platform.empty:
            # To avoid showing a warning for every single platform when a specific one is selected,
            # we check if the function's platform_name matches the active filter.
            if active_filters.get("Platform") and active_filters.get("Platform") != platform_name:
                pass # It's expected to be empty, so we do nothing.
            else:
                st.warning(f"No data available for {platform_name} with the current filters.")
            return

        df_platform["CTR"] = df_platform.apply(
            lambda row: row["Clicks"] / row["Impression"] if row.get("Impression") and row["Impression"] > 0 else 0,
            axis=1
        )

        # --- UI Rendering ---
        box_height = 200  # Increased height for better readability

        # Header
        headers = ["Format", "Creative Type", "Creative Length"]
        header_cols = st.columns([0.3, 0.3, 0.3, 4])
        for col, label in zip(header_cols[:-1], headers):
            col.markdown(f"**{label}**")
        header_cols[-1].markdown(f"**{metric_choice} Chart by Content**")

        # Group data by the three attributes to create a separate row for each combination
        grouped = df_platform.groupby(["Format", "Creative_Type", "Creative_Length"])

        for (format_val, type_val, length_val), group_df in grouped:
            # For each group, create a row in the UI
            data_cols = st.columns([0.3, 0.3, 0.3, 4])
            
            # Column 1: Format
            with data_cols[0]:
                st.markdown(f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: bold;'>{format_val}</div>", unsafe_allow_html=True)
            
            # Column 2: Creative Type
            with data_cols[1]:
                st.markdown(f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: bold;'>{type_val}</div>", unsafe_allow_html=True)
            
            # Column 3: Creative Length
            with data_cols[2]:
                st.markdown(f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: bold;'>{length_val}</div>", unsafe_allow_html=True)

            # Column 4: Chart
            with data_cols[3]:
                if group_df.empty:
                    st.warning("No content to display for this group.")
                    continue

                # Aggregate summary CTR and ctr_bm by Content
                agg_df = group_df.groupby("Content").agg({
                    "CTR": "mean",
                    "ctr_bm": "mean" if "ctr_bm" in group_df.columns else "min"
                }).reset_index()

                # Bar chart: CTR by Content
                bar = alt.Chart(agg_df).mark_bar().encode(
                    x=alt.X('Content:N', axis=alt.Axis(title='Content', labelAngle=0)),
                    y=alt.Y('CTR:Q', axis=alt.Axis(format=".2%", title="Value")),
                    color=alt.value("#21ba45"),
                    tooltip=[alt.Tooltip("Content", title="Content"), alt.Tooltip("CTR", title="CTR", format=".2%")]
                )
                text = bar.mark_text(align='center', baseline='bottom', dy=-5).encode(text=alt.Text('CTR:Q', format=".2%"))

                # Calculate the mean ctr_bm for the current group (Format, Creative_Type, Creative_Length)
                mean_ctr_bm = group_df["ctr_bm"].mean() if "ctr_bm" in group_df.columns else None
                if mean_ctr_bm is not None:
                    rule = alt.Chart(pd.DataFrame({'y': [mean_ctr_bm]})).mark_rule(color='red', strokeDash=[3,3]).encode(
                        y='y',
                        tooltip=[alt.Tooltip('y', title='Mean CTR_BM', format='.2%')]
                    )
                    # Position benchmark label completely outside the chart area (left margin)
                    rule_text = alt.Chart(pd.DataFrame({'y': [mean_ctr_bm], 'label': [f"BM: {mean_ctr_bm:.2%}"]})).mark_text(
                        align='right',
                        baseline='middle',
                        dx=-120,  # Move much further to the left, outside chart bounds
                        dy=0,     # Center vertically on the benchmark line
                        color='red',
                        fontWeight='bold',
                        fontSize=12,
                        clip=False
                    ).encode(
                        y='y:Q',
                        text='label:N'
                    )
                else:
                    rule = alt.Chart(pd.DataFrame({'y': []})).mark_rule()
                    rule_text = alt.Chart(pd.DataFrame({'y': []})).mark_text()

                chart = (bar + text + rule + rule_text).properties(
                    height=box_height,
                    padding={"left": 80, "top": 10, "right": 10, "bottom": 10}
                ).configure_view(strokeOpacity=0)
                st.altair_chart(chart, use_container_width=True)

def display(query_data, active_filters, start_date, end_date):
    with stylable_container(
        key="creative_container",
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
                    font-family: 'Arial', sans-serif;
                ">{campaign_name}</h1>
                <p style="
                    color: #B3D9FF;
                    margin: 0.5rem 0 0 0;
                    font-size: 1.2rem;
                    text-align: center;
                    font-weight: 400;
                    font-family: 'Arial', sans-serif;
                ">Creative Performance</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        # If a specific platform is selected in the sidebar, show only that analysis.
        # Otherwise, loop through all default platforms.
        if active_filters.get("Platform"):
            platforms_to_show = [active_filters["Platform"]]
        else:
            platforms_to_show = ["Facebook", "Google Ads", "Tiktok", "YouTube"]

        for platform in platforms_to_show:
            # Pass the specific platform name to the generation function.
            # The function will now correctly use this platform name ONLY if no platform is set in active_filters.
            generate_platform_analysis(platform, query_data, active_filters, start_date, end_date)

        # Creative Performance Data Table with Material-UI styling
        with stylable_container(
            key="creative_performance_container",
            css_styles="""
                {
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    padding: 1.25rem;
                    margin: 20px 0;
                }
            """,
        ):
            st.markdown("### CREATIVE PERFORMANCE DATA")

            
            # First, get the data grouped by content attributes (without thumbnail_url)
            aggrid_df = query_data(
                columns=[
                    "Content", "Creative_Type", "Format", "Creative_Length", 
                    "Brand", "Funnel", "Platform", "Audience", "Region", "Buying_Method",
                    "Cost", "Impression", "Clicks", "Views", "Engagements",
                    "ctr_bm", "vtr_bm", "er_bm"
                ],
                tablename="report_campaign_creative",
                filters=active_filters,
                start_date=start_date,
                end_date=end_date,
                aggregations={
                    "Cost": "SUM", "Impression": "SUM", "Clicks": "SUM", "Views": "SUM", "Engagements": "SUM",
                    "ctr_bm": "AVG", "vtr_bm": "AVG", "er_bm": "AVG"
                },
                group_by=[
                    "Content", "Creative_Type", "Format", "Creative_Length", 
                    "Brand", "Funnel", "Platform", "Audience", "Region", "Buying_Method"
                ]
            )

            # Get thumbnail URLs for each group
            thumbnail_df = query_data(
                columns=[
                    "thumbnail_url", "Content", "Creative_Type", "Format", "Creative_Length", 
                    "Brand", "Funnel", "Platform", "Audience", "Region", "Buying_Method"
                ],
            tablename="report_campaign_creative",
            filters=active_filters,
            start_date=start_date,
            end_date=end_date,
                aggregations={},
                group_by=[
                    "Content", "Creative_Type", "Format", "Creative_Length", 
                    "Brand", "Funnel", "Platform", "Audience", "Region", "Buying_Method"
                ]
            )
            
            # Select one thumbnail per group (first non-null thumbnail)
            if not thumbnail_df.empty:
                thumbnail_df = thumbnail_df.groupby([
                    "Content", "Creative_Type", "Format", "Creative_Length", 
                    "Brand", "Funnel", "Platform", "Audience", "Region", "Buying_Method"
                ]).agg({
                    'thumbnail_url': lambda x: x.dropna().iloc[0] if len(x.dropna()) > 0 else None
                }).reset_index()
                
                # Merge thumbnail URLs with the main data
                aggrid_df = aggrid_df.merge(
                    thumbnail_df, 
                    on=["Content", "Creative_Type", "Format", "Creative_Length", 
                        "Brand", "Funnel", "Platform", "Audience", "Region", "Buying_Method"],
                    how="left"
                )
            st.markdown(start_date)

            if not aggrid_df.empty:
                    # Calculate CTR for each row with proper type conversion and error handling
                    def safe_ctr_calculation(row):
                        try:
                            clicks = float(row["Clicks"]) if pd.notna(row["Clicks"]) else 0
                            impressions = float(row["Impression"]) if pd.notna(row["Impression"]) else 0
                            return (clicks / impressions * 100) if impressions > 0 else 0
                        except (ValueError, TypeError, ZeroDivisionError):
                            return 0
                    
                    aggrid_df["CTR"] = aggrid_df.apply(safe_ctr_calculation, axis=1)
                    
                    # Calculate CPM for each row with proper type conversion and error handling
                    def safe_cpm_calculation(row):
                        try:
                            cost = float(row["Cost"]) if pd.notna(row["Cost"]) else 0
                            impressions = float(row["Impression"]) if pd.notna(row["Impression"]) else 0
                            return (cost / (impressions / 1000)) if impressions > 0 else 0
                        except (ValueError, TypeError, ZeroDivisionError):
                            return 0
                    
                    aggrid_df["CPM"] = aggrid_df.apply(safe_cpm_calculation, axis=1)
                    
                    # Calculate VTR (View Through Rate) with proper type conversion and error handling
                    def safe_vtr_calculation(row):
                        try:
                            views = float(row["Views"]) if pd.notna(row["Views"]) else 0
                            impressions = float(row["Impression"]) if pd.notna(row["Impression"]) else 0
                            return (views / impressions * 100) if impressions > 0 else 0
                        except (ValueError, TypeError, ZeroDivisionError):
                            return 0
                    
                    aggrid_df["VTR"] = aggrid_df.apply(safe_vtr_calculation, axis=1)
                    
                    # Calculate ER (Engagement Rate) with proper type conversion and error handling
                    def safe_er_calculation(row):
                        try:
                            engagements = float(row["Engagements"]) if pd.notna(row["Engagements"]) else 0
                            impressions = float(row["Impression"]) if pd.notna(row["Impression"]) else 0
                            return (engagements / impressions * 100) if impressions > 0 else 0
                        except (ValueError, TypeError, ZeroDivisionError):
                            return 0
                    
                    aggrid_df["ER"] = aggrid_df.apply(safe_er_calculation, axis=1)
                    
                    # Helper function to safely format ctr_bm
                    def safe_format_ctr_bm(value):
                        try:
                            if pd.notna(value) and value is not None:
                                return f"{float(value)*100:.2f}%"
                            return ''
                        except (ValueError, TypeError):
                            return ''
                    
                    # Helper function to get thumbnail URL
                    def get_thumbnail_url(thumbnail_url):
                        if pd.notna(thumbnail_url) and thumbnail_url and thumbnail_url.strip():
                            return thumbnail_url.strip()
                        return None
                    
                    # Prepare table data with formatting
                    table_rows = []
                    for _, row in aggrid_df.iterrows():
                        table_rows.append([
                            get_thumbnail_url(row.get('thumbnail_url')),  # Thumbnail URL
                            row['Content'] or '',    # Content
                            row['Creative_Type'] or '',  # Creative type
                            row['Format'] or '',     # Creative format
                            row['Creative_Length'] or '',  # Creative length
                            row['Brand'] or '',      # Brand
                            row['Funnel'] or '',     # Funnel
                            row['Platform'] or '',   # Platform
                            row['Audience'] or '',   # Audience
                            row['Region'] or '',     # Region
                            row['Buying_Method'] or '',       # Buying Method
                            safe_format_ctr_bm(row.get('vtr_bm')),  # VTR Benchmark
                            f"{row['VTR']:.2f}%" if pd.notna(row['VTR']) else '',  # VTR
                            safe_format_ctr_bm(row.get('ctr_bm')),  # CTR Benchmark
                            f"{row['CTR']:.2f}%" if pd.notna(row['CTR']) else '',  # CTR
                            safe_format_ctr_bm(row.get('er_bm')),   # ER Benchmark
                            f"{row['ER']:.2f}%" if pd.notna(row['ER']) else '',   # ER
                        ])
                    
                    # Add summary row with proper type conversion and error handling
                    try:
                        total_impressions = float(aggrid_df['Impression'].sum()) if pd.notna(aggrid_df['Impression'].sum()) else 0
                        total_clicks = float(aggrid_df['Clicks'].sum()) if pd.notna(aggrid_df['Clicks'].sum()) else 0
                        total_views = float(aggrid_df['Views'].sum()) if pd.notna(aggrid_df['Views'].sum()) else 0
                        total_engagements = float(aggrid_df['Engagements'].sum()) if pd.notna(aggrid_df['Engagements'].sum()) else 0
                        
                        avg_vtr = (total_views / total_impressions * 100) if total_impressions > 0 else 0
                        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                        avg_er = (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
                        
                        avg_vtr_bm = float(aggrid_df['vtr_bm'].mean()) if pd.notna(aggrid_df['vtr_bm'].mean()) else 0
                        avg_ctr_bm = float(aggrid_df['ctr_bm'].mean()) if pd.notna(aggrid_df['ctr_bm'].mean()) else 0
                        avg_er_bm = float(aggrid_df['er_bm'].mean()) if pd.notna(aggrid_df['er_bm'].mean()) else 0
                    except (ValueError, TypeError, ZeroDivisionError):
                        avg_vtr = avg_ctr = avg_er = avg_vtr_bm = avg_ctr_bm = avg_er_bm = 0
                    
                    table_rows.append([
                        "TOTAL",  # Thumbnail
                        "",       # Content
                        "",       # Creative type
                        "",       # Creative format
                        "",       # Creative length
                        "",       # Brand
                        "",       # Funnel
                        "",       # Platform
                        "",       # Audience
                        "",       # Region
                        "",       # Buying Method
                        safe_format_ctr_bm(avg_vtr_bm),  # VTR Benchmark
                        f"{avg_vtr:.2f}%",  # VTR
                        safe_format_ctr_bm(avg_ctr_bm),  # CTR Benchmark
                        f"{avg_ctr:.2f}%",  # CTR
                        safe_format_ctr_bm(avg_er_bm),   # ER Benchmark
                        f"{avg_er:.2f}%",   # ER
                    ])

                    # Define table headers
                    headers = [
                        "Thumbnail", "Content", "Creative Type", "Creative Format", "Creative Length",
                        "Brand", "Funnel", "Platform", "Audience", "Region", "Buying Method",
                        "VTR Benchmark", "VTR", "CTR Benchmark", "CTR", "ER Benchmark", "ER"
                    ]

                    # Helper function to get cell color based on performance vs benchmark
                    def get_performance_color(actual_value, benchmark_value):
                        try:
                            if not actual_value or not benchmark_value or actual_value == '' or benchmark_value == '':
                                return "inherit"
                            actual = float(actual_value.replace('%', ''))
                            benchmark = float(benchmark_value.replace('%', ''))
                            if actual >= benchmark:
                                return "#28a745"  # Green for good performance
                            elif actual >= benchmark * 0.8:
                                return "#fd7e14"  # Orange for moderate performance
                            return "#dc3545"  # Red for poor performance
                        except:
                            return "inherit"

                    # Create Material-UI Table
                    with elements("creative_table"):
                        with mui.Paper(
                            elevation=0,
                            sx={
                                "margin": "20px 0",
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
                                                    # Special styling for performance columns
                                                    cell_color = "inherit"
                                                    font_weight = "bold" if is_summary else "normal"
                                                    
                                                    # Color coding for performance metrics vs benchmarks
                                                    if not is_summary and cell and cell != "":
                                                        # VTR vs VTR Benchmark (columns 11 and 12)
                                                        if j == 11:  # VTR column
                                                            benchmark_cell = row[12]  # VTR Benchmark column
                                                            cell_color = get_performance_color(cell, benchmark_cell)
                                                        # CTR vs CTR Benchmark (columns 13 and 14)
                                                        elif j == 13:  # CTR column
                                                            benchmark_cell = row[14]  # CTR Benchmark column
                                                            cell_color = get_performance_color(cell, benchmark_cell)
                                                        # ER vs ER Benchmark (columns 15 and 16)
                                                        elif j == 15:  # ER column
                                                            benchmark_cell = row[16]  # ER Benchmark column
                                                            cell_color = get_performance_color(cell, benchmark_cell)
                                                    
                                                    # Special handling for thumbnail column (first column)
                                                    if j == 0 and not is_summary and cell and cell != "":
                                                        # Render thumbnail image
                                                        mui.TableCell(
                                                            html.img(
                                                                src=cell,
                                                                style={
                                                                    "width": "60px",
                                                                    "height": "60px",
                                                                    "objectFit": "cover",
                                                                    "borderRadius": "4px"
                                                                }
                                                            ),
                                                            sx={
                                                                "textAlign": "center",
                                                                "padding": "6px 4px",
                                                                "borderBottom": "1px solid #e2e8f0",
                                                                "borderRight": "1px solid #e2e8f0"
                                                            }
                                                        )
                                                    elif j == 0 and not is_summary:
                                                        # No image available
                                                        mui.TableCell(
                                                            "No Image",
                                                            sx={
                                                                "textAlign": "center",
                                                                "padding": "6px 4px",
                                                                "fontSize": "0.7rem",
                                                                "color": "#666",
                                                                "borderBottom": "1px solid #e2e8f0",
                                                                "borderRight": "1px solid #e2e8f0"
                                                            }
                                                        )
                                                    elif j == 0 and is_summary:
                                                        # Summary row thumbnail cell
                                                        mui.TableCell(
                                                            "TOTAL",
                                                            sx={
                                                                "textAlign": "center",
                                                                "padding": "6px 4px",
                                                                "fontSize": "0.7rem",
                                                                "fontWeight": "bold",
                                                                "backgroundColor": "#003366",
                                                                "color": "white",
                                                                "borderBottom": "1px solid #e2e8f0",
                                                                "borderRight": "1px solid #e2e8f0"
                                                            }
                                                        )
                                                    else:
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
            else:
                st.warning("No detailed creative data to display.")
