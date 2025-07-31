import streamlit as st
import pandas as pd
import altair as alt
from streamlit_extras.stylable_container import stylable_container
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def display(query_data, active_filters, start_date, end_date):
    with stylable_container(
        key="creative_container",
        css_styles="""
            {
                animation: fadeIn 0.5s ease-in-out;
            }
            """,
    ):
        st.title("Creative Benchmark Analysis")

        # Using hardcoded data as per the original source
        platforms = {
            "Facebook": [
                {"format": "VRC", "type": "Image", "length": "NA", "ctr": 0.04},
                {"format": "VRC", "type": "Video", "length": "6S", "ctr": 0.06},
                {"format": "VVC", "type": "Video", "length": "15S", "ctr": 0.06},

            ],
            "Google": [
                {"format": "VRC", "type": "Image", "length": "NA", "ctr": 0.04},
                {"format": "VRC", "type": "Video", "length": "6S", "ctr": 0.06},
                {"format": "VVC", "type": "Video", "length": "15S", "ctr": 0.06},
            ],
            "Tiktok": [
                {"format": "VRC", "type": "Image", "length": "NA", "ctr": 0.04},
                {"format": "VRC", "type": "Video", "length": "6S", "ctr": 0.06},
                {"format": "VVC", "type": "Video", "length": "15S", "ctr": 0.06},            ]
        }

        for platform, rows in platforms.items():
            with stylable_container(
                key=f"{platform.lower()}BenchmarkAnalysis",
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
                    st.header(f"{platform} Benchmark Analysis")
                with col2:
                    st.selectbox(label="Select metrics", options=["CTR", "VTR"], key=f"{platform.lower()}_metric_selectbox")

                benchmark_value = 0.05
                box_height = 100

                headers = ["Format", "Creative Type", "Creative Length"]
                header_cols = st.columns([1, 1, 1, 4])
                for col, label in zip(header_cols, headers):
                    col.markdown(f"**{label}**")
                
                for row in rows:
                    data_cols = st.columns([1, 1, 1, 4])
                    with data_cols[0]:
                        st.markdown(f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; justify-content: center; border-radius: 8px;'>{row['format']}</div>", unsafe_allow_html=True)
                    with data_cols[1]:
                        st.markdown(f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; justify-content: center; border-radius: 8px;'>{row['type']}</div>", unsafe_allow_html=True)
                    with data_cols[2]:
                        st.markdown(f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; justify-content: center; border-radius: 8px;'>{row['length']}</div>", unsafe_allow_html=True)
                    with data_cols[3]:
                        df_chart = pd.DataFrame([{"Label": row["length"], "CTR": row["ctr"]}])
                        df_chart["Color"] = df_chart["CTR"].apply(lambda x: "green" if x >= benchmark_value else "red")
                        
                        bar = alt.Chart(df_chart).mark_bar().encode(
                            x=alt.X('Label:N', axis=alt.Axis(title=None, labels=False)),
                            y=alt.Y('CTR:Q', axis=alt.Axis(format=".0%")),
                            color=alt.Color('Color:N', scale=None)
                        )
                        
                        text = bar.mark_text(align='center', baseline='bottom', dy=-5).encode(text=alt.Text('CTR:Q', format=".1%"))
                        
                        rule = alt.Chart(pd.DataFrame({'y': [benchmark_value]})).mark_rule(color='red', strokeDash=[3,3]).encode(y='y')
                        
                        chart = (bar + text + rule).properties(height=box_height).configure_view(strokeOpacity=0)
                        st.altair_chart(chart, use_container_width=True)

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
            aggrid_df["CTR"] = aggrid_df.apply(
                lambda row: row["Clicks"] / row["Impression"] if row.get("Impression") and row["Impression"] > 0 else 0,
                axis=1
            )

            custom_css = {
                ".ag-header-cell-label": {
                    "font-size": "14px",
                    "font-weight": "600",
                    "color": "#FFFFFF",
                    "white-space": "normal",
                    "line-height": "1.2",
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
            
            gb = GridOptionsBuilder.from_dataframe(aggrid_df)
            gb.configure_default_column(
                resizable=True,
                filterable=True,
                sortable=True,
                editable=False,
            )

            percentage_formatter = JsCode("""
                function(params) {
                    if (params.value === null || typeof params.value === 'undefined') {
                        return '';
                    }
                    return (params.value * 100).toFixed(2) + '%';
                }
            """)

            ctr_style_jscode = JsCode("""
                function(params) {
                    if (params.value === null || params.data.ctr_bm === null) {
                        return { 'color': 'black' };
                    }
                    if (params.value > params.data.ctr_bm) {
                        return {
                            'color': '#28A745',
                            'fontWeight': '600',
                        };
                    } else if (params.value < params.data.ctr_bm) {
                        return {
                            'color': '#DC3545',
                            'fontWeight': '600',
                        };
                    }
                    return { 'color': 'black' };
                }
            """)

            gb.configure_column("Cost", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Cost.toLocaleString('en-US')")
            gb.configure_column("Impression", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Impression.toLocaleString('en-US')")
            gb.configure_column("Clicks", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Clicks.toLocaleString('en-US')")
            gb.configure_column("CTR", headerName="CTR", valueFormatter=percentage_formatter, cellStyle=ctr_style_jscode)
            gb.configure_column("ctr_bm", headerName="CTR Benchmark", valueFormatter=percentage_formatter)

            gridOptions = gb.build()

            if not aggrid_df.empty:
                cost_sum = aggrid_df['Cost'].sum()
                impressions_sum = aggrid_df['Impression'].sum()
                clicks_sum = aggrid_df['Clicks'].sum()
                
                summary_row = {
                    "Platform": "Total",
                    "Cost": int(cost_sum),
                    "Impression": int(impressions_sum),
                    "Clicks": int(clicks_sum),
                    "CTR": (clicks_sum / impressions_sum) if impressions_sum > 0 else 0,
                    "ctr_bm": aggrid_df['ctr_bm'].mean()
                }
                
                gridOptions['pinnedBottomRowData'] = [summary_row]

            AgGrid(
                aggrid_df,
                gridOptions=gridOptions,
                allow_unsafe_jscode=True,
                enable_enterprise_modules=False,
                theme='ag-theme-quartz',
                custom_css=custom_css,
                height=600,
                width='100%',
                reload_data=True,
                column_auto_size_strategy="FIT_CONTENTS"
            )
        else:
            st.warning("No detailed creative data to display.")
