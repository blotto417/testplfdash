import streamlit as st
import pandas as pd
import altair as alt
from streamlit_extras.stylable_container import stylable_container
from st_aggrid import AgGrid, GridOptionsBuilder

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
            st.warning(f"No data available for {platform_name} with the current filters.")
            return

        df_platform["CTR"] = df_platform.apply(
            lambda row: row["Clicks"] / row["Impression"] if row.get("Impression") and row["Impression"] > 0 else 0,
            axis=1
        )

        # --- UI Rendering ---
        benchmark_value = 0.05
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
                    rule_text = alt.Chart(pd.DataFrame({'y': [mean_ctr_bm], 'label': [f"BM: {mean_ctr_bm:.2%}"]})).mark_text(
                        align='left',
                        baseline='bottom',
                        dx=0,
                        dy=20,  # Move the label down into the chart area
                        color='red',
                        fontWeight='bold',
                        clip=False
                    ).encode(
                        y='y',
                        text='label:N'
                    )
                else:
                    rule = alt.Chart(pd.DataFrame({'y': []})).mark_rule()
                    rule_text = alt.Chart(pd.DataFrame({'y': []})).mark_text()

                chart = (bar + text + rule + rule_text).properties(height=box_height).configure_view(strokeOpacity=0)
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

        platforms_to_show = ["Facebook", "Google", "Tiktok"]
        for platform in platforms_to_show:
            generate_platform_analysis(platform, query_data, active_filters, start_date, end_date)

        st.subheader("Creative Performance Data")
        aggrid_df = query_data(
            columns=["Format", "Creative_Type", "Creative_Length", "Platform", "Region", "Audience", "Cost", "Impression", "Clicks", "ctr_bm"],
            tablename="report_campaign_creative",
            filters=active_filters,
            start_date=start_date,
            end_date=end_date,
            aggregations={"Cost": "SUM", "Impression": "SUM", "Clicks": "SUM", "ctr_bm": "AVG"},
            group_by=["Format", "Creative_Type", "Creative_Length", "Platform", "Region", "Audience"]
        )

        if not aggrid_df.empty:
            gb = GridOptionsBuilder.from_dataframe(aggrid_df)
            gb.configure_column("Cost", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Cost.toLocaleString('en-US')")
            gb.configure_column("Impression", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Impression.toLocaleString('en-US')")
            AgGrid(aggrid_df, gridOptions=gb.build(), theme="ag-theme-quartz", height=600)
        else:
            st.warning("No detailed creative data to display.")
