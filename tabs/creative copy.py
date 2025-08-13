import streamlit as st
import pandas as pd
import altair as alt
from streamlit_extras.stylable_container import stylable_container
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def display(query_data, active_filters, start_date, end_date):

    with stylable_container(
        key="faceBookBenchmarkAnalysis",
        css_styles="""

            { 
                background-color: white;
                border-radius: 0.5em;                
                padding: 0.5em;}

            hr {
                border-bottom: 5px solid white;
            }
            """,
        ):
        colfb1, colfb2 = st.columns([3, 1])
        with colfb1:
            st.title("FaceBook Benchmark Analysis")
        with colfb2:
            choice = st.selectbox(label="Select metrics", options=["CTR", "VTR", "VTR 2/3S"], key="GGmetricselectbox")

        # Sample input (replace with your grouped data)
        rows = [
            {"channel": "YouTube", "format": "VRC", "type": "Image", "length": "NA", "ctr": 0.04},
            {"channel": "YouTube", "format": "VRC", "type": "Video", "length": "6S", "ctr": 0.06},
            {"channel": "YouTube", "format": "VVC", "type": "Video", "length": "15S", "ctr": 0.08},
        ]

        benchmark_value = 0.05
        box_height = 100
        box_spacing = 10

        # Header labels for the first 3 columns
        headers = ["Format", "Creative Type", "Creative Length"]
        cols = st.columns([1, 1, 1, 4])

        # Render static headers
        for col, label in zip(cols[:-1], headers):
            col.markdown(
                f"<div style='height: 40px; display: flex; align-items: center; justify-content: center; "
                f"font-size: 20px; font-weight: bold;'>{label}</div>",
                unsafe_allow_html=True
            )

        # Render selectbox in the last column
        with cols[-1]:
            st.markdown(
                """
            <div style='height: 40px; display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: bold;'>
                    Chart
                </div>
                """,
                unsafe_allow_html=True
            )
        # Data rows
        for row in rows:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 4])

            # col1 - Format
            with col1:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['format']}</div>",
                    unsafe_allow_html=True
                )

            # col2 - Creative Type
            with col2:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['type']}</div>",
                    unsafe_allow_html=True
                )

            # col3 - Creative Length
            with col3:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['length']}</div>",
                    unsafe_allow_html=True
                )

            # col4 - Chart
            with col4:
                df = pd.DataFrame({"Label": [row["length"]], "CTR": [row["ctr"]]})
                df["Color"] = df["CTR"].apply(lambda x: "green" if x >= benchmark_value else "red")

                bar = alt.Chart(df).mark_bar().encode(
                    x=alt.X('Label:N', axis=alt.Axis(title=None, labelAngle=0)),
                    y=alt.Y('CTR:Q', axis=alt.Axis(format=".0%", title="CTR")),
                    color=alt.Color('Color:N', scale=None),
                    tooltip=["Label", alt.Tooltip("CTR", format=".2%")]
                )

                bar_text = alt.Chart(df).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-2,
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    x='Label:N',
                    y='CTR:Q',
                    text=alt.Text('CTR:Q', format=".2%")
                )

                benchmark_df = pd.DataFrame({"y": [benchmark_value]})
                benchmark = alt.Chart(benchmark_df).mark_rule(
                    color="red", strokeDash=[4, 4]
                ).encode(
                    y='y:Q'
                )
                benchmark_label = alt.Chart(benchmark_df).mark_text(
                    text=f"{benchmark_value:.2%}",
                    align='left',
                    baseline='bottom',
                    dx=0,
                    x=0,  # <-- Directly set position here
                    color='red',
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    y='y:Q'
                )

                chart = (bar + bar_text + benchmark + benchmark_label).properties(
                    height=box_height,
                    width='container'
                ).configure_view(stroke=None, 
                ).configure(background = 'white')

                st.altair_chart(chart, use_container_width=True)

    with stylable_container(
        key="googlekBenchmarkAnalysis",
        css_styles="""

            { 
                background-color: white;
                border-radius: 0.5em;                
                padding: 0.5em;}

            hr {
                border-bottom: 5px solid white;
            }
            """,
        ):
        colgg1, colgg2 = st.columns([3, 1])
        with colgg1:
            st.title("Google Benchmark Analysis")
        with colgg2:
            choice = st.selectbox(label="Select metrics", options=["CTR", "VTR", "VTR 2/3S"], key="FBmetricselectbox")

        # Sample input (replace with your grouped data)
        rows = [
            {"channel": "YouTube", "format": "VRC", "type": "Image", "length": "NA", "ctr": 0.04},
            {"channel": "YouTube", "format": "VRC", "type": "Video", "length": "6S", "ctr": 0.06},
            {"channel": "YouTube", "format": "VVC", "type": "Video", "length": "15S", "ctr": 0.08},
        ]

        benchmark_value = 0.05
        box_height = 100
        box_spacing = 10

        # Header labels for the first 3 columns
        headers = ["Format", "Creative Type", "Creative Length"]
        cols = st.columns([1, 1, 1, 4])

        # Render static headers
        for col, label in zip(cols[:-1], headers):
            col.markdown(
                f"<div style='height: 40px; display: flex; align-items: center; justify-content: center; "
                f"font-size: 20px; font-weight: bold;'>{label}</div>",
                unsafe_allow_html=True
            )

        # Render selectbox in the last column
        with cols[-1]:
            st.markdown(
                """
            <div style='height: 40px; display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: bold;'>
                    Chart
                </div>
                """,
                unsafe_allow_html=True
            )
        # Data rows
        for row in rows:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 4])

            # col1 - Format
            with col1:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['format']}</div>",
                    unsafe_allow_html=True
                )

            # col2 - Creative Type
            with col2:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['type']}</div>",
                    unsafe_allow_html=True
                )

            # col3 - Creative Length
            with col3:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['length']}</div>",
                    unsafe_allow_html=True
                )

            # col4 - Chart
            with col4:
                df = pd.DataFrame({"Label": [row["length"]], "CTR": [row["ctr"]]})
                df["Color"] = df["CTR"].apply(lambda x: "green" if x >= benchmark_value else "red")

                bar = alt.Chart(df).mark_bar().encode(
                    x=alt.X('Label:N', axis=alt.Axis(title=None, labelAngle=0)),
                    y=alt.Y('CTR:Q', axis=alt.Axis(format=".0%", title="CTR")),
                    color=alt.Color('Color:N', scale=None),
                    tooltip=["Label", alt.Tooltip("CTR", format=".2%")]
                )

                bar_text = alt.Chart(df).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-2,
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    x='Label:N',
                    y='CTR:Q',
                    text=alt.Text('CTR:Q', format=".2%")
                )

                benchmark_df = pd.DataFrame({"y": [benchmark_value]})
                benchmark = alt.Chart(benchmark_df).mark_rule(
                    color="red", strokeDash=[4, 4]
                ).encode(
                    y='y:Q'
                )
                benchmark_label = alt.Chart(benchmark_df).mark_text(
                    text=f"{benchmark_value:.2%}",
                    align='left',
                    baseline='bottom',
                    dx=0,
                    x=0,  # <-- Directly set position here
                    color='red',
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    y='y:Q'
                )

                chart = (bar + bar_text + benchmark + benchmark_label).properties(
                    height=box_height,
                    width='container'
                ).configure_view(stroke=None, 
                ).configure(background = 'white')

                st.altair_chart(chart, use_container_width=True)
    # Tiktok
    with stylable_container(
        key="tiktokBenchmarkAnalysis",
        css_styles="""

            { 
                background-color: white;
                border-radius: 0.5em;                
                padding: 0.5em;}

            hr {
                border-bottom: 5px solid white;
            }
            """,
        ):
        coltt1, coltt2 = st.columns([3, 1])
        with coltt1:
            st.title("Tiktok Benchmark Analysis")
        with coltt2:
            choice = st.selectbox(label="Select metrics", options=["CTR", "VTR", "VTR 2/3S"], key="TTmetricselectbox")

        # Sample input (replace with your grouped data)
        rows = [
            {"channel": "YouTube", "format": "VRC", "type": "Image", "length": "NA", "ctr": 0.04},
            {"channel": "YouTube", "format": "VRC", "type": "Video", "length": "6S", "ctr": 0.06},
            {"channel": "YouTube", "format": "VVC", "type": "Video", "length": "15S", "ctr": 0.08},
        ]

        benchmark_value = 0.05
        box_height = 100
        box_spacing = 10

        # Header labels for the first 3 columns
        headers = ["Format", "Creative Type", "Creative Length"]
        cols = st.columns([1, 1, 1, 4])

        # Render static headers
        for col, label in zip(cols[:-1], headers):
            col.markdown(
                f"<div style='height: 40px; display: flex; align-items: center; justify-content: center; "
                f"font-size: 20px; font-weight: bold;'>{label}</div>",
                unsafe_allow_html=True
            )

        # Render selectbox in the last column
        with cols[-1]:
            st.markdown(
                """
            <div style='height: 40px; display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: bold;'>
                    Chart
                </div>
                """,
                unsafe_allow_html=True
            )
        # Data rows
        for row in rows:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 4])

            # col1 - Format
            with col1:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['format']}</div>",
                    unsafe_allow_html=True
                )

            # col2 - Creative Type
            with col2:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['type']}</div>",
                    unsafe_allow_html=True
                )

            # col3 - Creative Length
            with col3:
                st.markdown(
                    f"<div style='background-color:#f0f0f0; height: {box_height}px; display: flex; align-items: center; "
                    f"justify-content: center; border-radius: 8px; font-weight: bold;'>{row['length']}</div>",
                    unsafe_allow_html=True
                )

            # col4 - Chart
            with col4:
                df = pd.DataFrame({"Label": [row["length"]], "CTR": [row["ctr"]]})
                df["Color"] = df["CTR"].apply(lambda x: "green" if x >= benchmark_value else "red")

                bar = alt.Chart(df).mark_bar().encode(
                    x=alt.X('Label:N', axis=alt.Axis(title=None, labelAngle=0)),
                    y=alt.Y('CTR:Q', axis=alt.Axis(format=".0%", title="CTR")),
                    color=alt.Color('Color:N', scale=None),
                    tooltip=["Label", alt.Tooltip("CTR", format=".2%")]
                )

                bar_text = alt.Chart(df).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-2,
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    x='Label:N',
                    y='CTR:Q',
                    text=alt.Text('CTR:Q', format=".2%")
                )

                benchmark_df = pd.DataFrame({"y": [benchmark_value]})
                benchmark = alt.Chart(benchmark_df).mark_rule(
                    color="red", strokeDash=[4, 4]
                ).encode(
                    y='y:Q'
                )
                benchmark_label = alt.Chart(benchmark_df).mark_text(
                    text=f"{benchmark_value:.2%}",
                    align='left',
                    baseline='bottom',
                    dx=0,
                    x=0,  # <-- Directly set position here
                    color='red',
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    y='y:Q'
                )

                chart = (bar + bar_text + benchmark + benchmark_label).properties(
                    height=box_height,
                    width='container'
                ).configure_view(stroke=None, 
                ).configure(background = 'white')

                st.altair_chart(chart, use_container_width=True) 

    aggregations_tablecreative={"Cost": "SUM", "Impression": "SUM", "Clicks": "SUM", "ctr_bm": "AVG"}
    group_by_tablecreative=["Format", "Creative_Type", "Creative_Length", "Platform", "Region", "Audience"]
    # === YouTube Column ===
    with st.container(key="benchmark_creative"):
        st.title("Benchmark Creative")
        columns = ["Format", "Creative_Type", "Creative_Length", "Platform", "Region", "Audience", "Cost", "Impression", "Clicks", "ctr_bm"]

        df_yt = query_data(columns, "report_campaign_creative", active_filters, start_date, end_date, aggregations_tablecreative, group_by_tablecreative).reset_index(drop=True)

        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
        gb_yt = GridOptionsBuilder.from_dataframe(df_yt)
        gb_yt.configure_column("Cost", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Cost.toLocaleString('en-US')")
        gb_yt.configure_column("Impression", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], valueFormatter="data.Impression.toLocaleString('en-US')")

        gb_yt.configure_default_column(
    floating_filter=True,
    min_column_width=10,
    maxWidth=110,
    # headerComponentParams={
    #     "template":
    #         '<div class="ag-cell-label-container" role="presentation">' +
    #         '  <span ref="eMenu" class="ag-header-icon ag-header-cell-menu-button"></span>' +
    #         '  <div ref="eLabel" class="ag-header-cell-label" role="presentation">' +
    #         '    <span ref="eSortOrder" class="ag-header-icon ag-sort-order"></span>' +
    #         '    <span ref="eSortAsc" class="ag-header-icon ag-sort-ascending-icon"></span>' +
    #         '    <span ref="eSortDesc" class="ag-header-icon ag-sort-descending-icon"></span>' +
    #         '    <span ref="eSortNone" class="ag-header-icon ag-sort-none-icon"></span>' +
    #         '    <span ref="eText" class="ag-header-cell-text" role="columnheader" style="white-space: normal;text-align: right;"></span>' +
    #         '    <span ref="eFilter" class="ag-header-icon ag-filter-icon"></span>' +
    #         '  </div>' +
    #         '</div>'
    # }   
    cellStyle = JsCode(
        r"""
        function(cellClassParams) {
            if (cellClassParams.data.gold > 3) {
                return {'background-color': 'gold'}
            }
            return {};
            }
    """)
)
       
        AgGrid(df_yt, gridOptions=gb_yt.build(), theme= "ag-theme-quartz", height=600, width="100%", allow_unsafe_jscode=True)                        
