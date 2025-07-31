import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_extras.stylable_container import stylable_container

def display(query_data, active_filters, start_date, end_date, selected_platform):
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
            "Audience", "Region", "impression_plan", "Impression", "reach_plan", "reach",
            "net_media_cost", "Cost", "views_plan", "Views", "click_plan", "Clicks",
            "plan_active_day", "active_day", "Engagements", "23s_Video_Views", 
            "Video_Plays_100", "ctr_estimate", "er_estimate", "sessions", "add_to_carts", 
            "ecommerce_purchases"
        ]
        
        # Query data from database
        df = query_data(
            columns=columns,
            tablename="report_campaign_overall_total",
            filters=active_filters,
            start_date=start_date,
            end_date=end_date,
            aggregations={
                # Plan data (average)
                "impression_plan": "AVG", "reach_plan": "AVG", "net_media_cost": "AVG",
                "views_plan": "AVG", "click_plan": "AVG", "plan_active_day": "AVG",
                "ctr_estimate": "AVG", "er_estimate": "AVG",
                # Actual data (sum)
                "Impression": "SUM", "reach": "SUM", "Cost": "SUM", "Views": "SUM", 
                "Clicks": "SUM", "active_day": "SUM", "Engagements": "SUM", 
                "23s_Video_Views": "SUM", "Video_Plays_100": "SUM", "sessions": "SUM",
                "add_to_carts": "SUM", "ecommerce_purchases": "SUM"
            },
            group_by=["Audience", "Region"]
        )
        
        if df.empty:
            st.warning("No data available for the selected filters.")
            return
        
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
        
        # Define metrics
        metrics = ["Impression", "Reach", "Budget", "Views", "Clicks", "Run Rate"]
        
        # Create delivery data dictionary
        delivery_data = {}
        for audience in all_audiences:
            audience_row = df[df['Combined_Audience'] == audience].iloc[0]
            delivery_data[audience] = [
                min(audience_row['impression_delivery'], 120),  # Cap at 120% for display
                min(audience_row['reach_delivery'], 120),
                min(audience_row['budget_delivery'], 120),
                min(audience_row['views_delivery'], 120),
                min(audience_row['clicks_delivery'], 120),
                min(audience_row['run_rate_delivery'], 120)
            ]
        
        # Filter audiences based on selection
        if selected_audience == "All Audiences":
            audiences_to_show = all_audiences
        else:
            audiences_to_show = [selected_audience]
        
        # Create individual charts for each audience
        # Color palette for different metrics
        metric_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
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
                            text=[f"{val}%" for val in audience_data],
                            textposition='inside',
                            showlegend=False,
                            hovertemplate='Achieved: %{y}%<br>Planned: 100%<extra></extra>'
                        ))
                        
                        # Update layout for individual chart
                        fig.update_layout(
                            title=f"{audience}",
                            xaxis_title="Metrics",
                            yaxis_title="Percentage (%)",
                            yaxis=dict(range=[0, max(120, max(audience_data) + 10)]),
                            height=400,
                            showlegend=False,
                            barmode='overlay',  # Overlay bars to show achievement over planned
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        # Rotate x-axis labels for better readability
                        fig.update_xaxes(tickangle=45)
                        
                        st.plotly_chart(fig, use_container_width=True)
        
        # Bottom Section: Efficiency and Effectiveness Tables
        st.markdown("---")
        
        # Create two columns for the tables
        col1, col2 = st.columns(2)
        
        with col1:
            with stylable_container(
                key="vmk_efficiency_container",
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
                st.subheader("EFFICIENCY")
                
                # Create efficiency table from real data
                efficiency_list = []
                audiences_to_show_table = all_audiences if selected_audience == "All Audiences" else [selected_audience]
                
                for audience in audiences_to_show_table:
                    audience_row = df[df['Combined_Audience'] == audience].iloc[0]
                    
                    # Calculate rates
                    view_2s_3s_rate = (audience_row['23s_Video_Views'] / audience_row['Impression'] * 100) if audience_row['Impression'] > 0 else 0
                    thru_play_rate = (audience_row['Video_Plays_100'] / audience_row['Views'] * 100) if audience_row['Views'] > 0 else 0
                    view_100_rate = (audience_row['Video_Plays_100'] / audience_row['Impression'] * 100) if audience_row['Impression'] > 0 else 0
                    ctr = (audience_row['Clicks'] / audience_row['Impression'] * 100) if audience_row['Impression'] > 0 else 0
                    er = (audience_row['Engagements'] / audience_row['Impression'] * 100) if audience_row['Impression'] > 0 else 0
                    
                    efficiency_list.append({
                        "Audience": audience,
                        "View 2s/3s Rate": f"{view_2s_3s_rate:.2f}%",
                        "Thru play rate": f"{thru_play_rate:.2f}%", 
                        "100% View Rate": f"{view_100_rate:.2f}%",
                        "CTR": f"{ctr:.2f}%",
                        "ER": f"{er:.2f}%"
                    })
                
                efficiency_df = pd.DataFrame(efficiency_list)
                
                # Apply conditional formatting
                def highlight_efficiency(val):
                    if isinstance(val, str) and val.endswith('%'):
                        try:
                            num_val = float(val.rstrip('%'))
                            if num_val >= 70:  # Highlight values >= 70%
                                return 'background-color: lightgreen'
                        except:
                            pass
                    return ''
                
                st.dataframe(
                    efficiency_df.style.applymap(highlight_efficiency),
                    use_container_width=True,
                    hide_index=True
                )
        
        with col2:
            with stylable_container(
                key="vmk_effectiveness_container",
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
                st.subheader("EFFECTIVENESS")
                
                # Create effectiveness table from real data
                effectiveness_list = []
                
                for audience in audiences_to_show_table:
                    audience_row = df[df['Combined_Audience'] == audience].iloc[0]
                    
                    # Calculate cost metrics
                    cpm = (audience_row['Cost'] / audience_row['Impression'] * 1000) if audience_row['Impression'] > 0 else 0
                    cpv = (audience_row['Cost'] / audience_row['Views']) if audience_row['Views'] > 0 else 0
                    cpcv = (audience_row['Cost'] / audience_row['Video_Plays_100']) if audience_row['Video_Plays_100'] > 0 else 0
                    cpc = (audience_row['Cost'] / audience_row['Clicks']) if audience_row['Clicks'] > 0 else 0
                    cpe = (audience_row['Cost'] / audience_row['Engagements']) if audience_row['Engagements'] > 0 else 0
                    
                    effectiveness_list.append({
                        "Audience": audience,
                        "CPM": f"{cpm:,.0f}",
                        "CPV": f"{cpv:,.0f}",
                        "CPCV": f"{cpcv:,.0f}",
                        "CPC": f"{cpc:,.0f}",
                        "CPE": f"{cpe:,.0f}"
                    })
                
                effectiveness_df = pd.DataFrame(effectiveness_list)
                
                # Apply conditional formatting for effectiveness
                def highlight_effectiveness(val):
                    if isinstance(val, str) and val.replace(',', '').isdigit():
                        try:
                            num_val = int(val.replace(',', ''))
                            if num_val <= 1500:  # Highlight lower cost values
                                return 'background-color: lightgreen'
                        except:
                            pass
                    return ''
                
                st.dataframe(
                    effectiveness_df.style.applymap(highlight_effectiveness),
                    use_container_width=True,
                    hide_index=True
                )
        
        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)